"""
session.py — Orchestrates a recall.ai Zoom interview session.

Flow:
  1. Create a recall.ai bot that joins the given Zoom URL
  2. In parallel:
     a. Poll recall.ai until the bot is live in the call
     b. Init ElevenLabs TTS, build the audio bridge, init the InterviewBot,
        run LLM prefetch, and generate all TTS audio
  3. Once both tracks complete, run the InterviewBot state machine
  4. Print the transcript and leave the call
"""

import os
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

# ── Environment ────────────────────────────────────────────────────────────────
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

# ── interview_bot on the path ──────────────────────────────────────────────────
_INTERVIEW_BOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_INTERVIEW_BOT_DIR))
sys.path.insert(0, str(Path(__file__).parent))

from pyngrok import conf as _ngrok_conf
from recall_client import RecallClient
import audio_bridge as audio_bridge
import db_client
import face_channel

# Single local port for the combined audio (/audio) + face (/face) WS gateway,
# exposed through one ngrok tunnel.
_WS_GATEWAY_PORT = 8766

# Configure ngrok auth token at import time so it's ready before the tunnel is needed.
_ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
if _ngrok_auth_token:
    _ngrok_conf.get_default().auth_token = _ngrok_auth_token


def _start_ws_gateway(port: int) -> str:
    """Serve both WebSocket handlers on one port and expose it via one ngrok tunnel.

    Routes by request path:
      /audio → recall.ai per-participant PCM stream (audio_ws_server._handler)
      /face  → bot-face visualisation events     (face_channel._handler)

    Multiplexing onto a single tunnel keeps us within ngrok's simultaneous-tunnel
    limit. Returns the base wss:// URL; callers append /audio or /face.
    """
    import asyncio
    import threading
    import websockets
    from pyngrok import ngrok
    import audio_ws_server

    async def _dispatch(websocket):
        path = websocket.request.path or ""
        if path.startswith("/face"):
            await face_channel._handler(websocket)
        else:
            await audio_ws_server._handler(websocket)

    async def _serve():
        async with websockets.serve(_dispatch, "0.0.0.0", port):
            await asyncio.Future()  # run forever

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        face_channel.attach_loop(loop)  # so face_channel.emit() broadcasts on this loop
        loop.run_until_complete(_serve())

    threading.Thread(target=_run, daemon=True).start()
    print(f"[ws] Gateway listening on port {port} (/audio + /face)", flush=True)

    # ngrok HTTP tunnels carry WebSocket upgrades and forward the path; swap scheme.
    tunnel = ngrok.connect(port, "http")
    base = tunnel.public_url.replace("https://", "wss://").replace("http://", "wss://")
    print(f"[ws] Public base URL: {base}", flush=True)
    return base


def _finish(interview_id: int, status: str, transcript: str | None) -> None:
    """Write terminal status + transcript via the finish endpoint, then mark.

    Never re-raises — a DB-write or marking failure must not mask the original
    interview outcome.
    """
    saved = False
    try:
        db_client.finish_interview(interview_id, status, transcript)
        saved = True
        print(f"[zoom] Interview {interview_id} finished → {status!r}", flush=True)
    except Exception as exc:
        print(
            f"[zoom] ERROR: could not write finish status {status!r} for interview {interview_id}: {exc}",
            file=sys.stderr,
            flush=True,
        )

    # Only mark completed interviews, and only once the transcript is safely in
    # the DB — the marker re-fetches the transcript from the DB by interview_id,
    # then publishes the grade + feedback report back to the DB as a Result.
    if status == "COMPLETED" and saved:
        _mark(interview_id)


def _mark(interview_id: int) -> None:
    """Run the marking bot for a finished interview.

    The marker fetches the stored transcript + rubric from the DB, grades it,
    and POSTs a Result record back. Never re-raises — a marking failure must
    not mask the interview outcome.
    """
    print(f"[zoom] Triggering marking bot for interview {interview_id}…", flush=True)
    try:
        from marker import mark_interview
        result_id = mark_interview(interview_id)
        print(f"[zoom] Marking complete → result ID {result_id}", flush=True)
    except Exception as exc:
        print(
            f"[zoom] ERROR: marking bot failed for interview {interview_id}: {exc}",
            file=sys.stderr,
            flush=True,
        )


def _format_transcript(entries: list) -> str:
    from transcript_format import format_transcript
    return format_transcript(entries)


def _install_thinking_hook() -> None:
    """Wrap InterviewBot._step so the face shows 'thinking' while a follow-up is
    being generated by the LLM. Non-invasive — no edit to bot.py (mirrors the
    same _step-wrapping trick test_runner.py uses)."""
    from bot import InterviewBot
    from context import InterviewState

    if getattr(InterviewBot._step, "_face_wrapped", False):
        return
    _orig_step = InterviewBot._step

    def _step(self, state):
        if state == InterviewState.FOLLOW_UP:
            face_channel.set_state("thinking")
        return _orig_step(self, state)

    _step._face_wrapped = True
    InterviewBot._step = _step


def run_zoom_interview(zoom_url: str, bot_name: str = "Interview Bot", interview_id: int | None = None) -> None:
    client = RecallClient()

    # ── 0. Start the combined audio + face WebSocket gateway (one ngrok tunnel)
    from config import cfg as _cfg, get_student
    _install_thinking_hook()

    ws_base = _start_ws_gateway(_WS_GATEWAY_PORT)
    audio_ws_url = ws_base + "/audio"
    face_ws_url = ws_base + "/face"

    face_channel.set_state("ready")
    try:
        face_channel.meta(get_student(_cfg)["name"])
    except Exception:
        pass

    # Operator-facing: where to point the local visualisation page. The remote
    # (wss) URL works from any machine — including when this bot runs on ECS.
    print("\n" + "=" * 70, flush=True)
    print("[face] Bot-face visualisation channel is live. Open the page and point it here:", flush=True)
    print(f"[face]   Remote/ECS : http://localhost:8080/?ws={face_ws_url}", flush=True)
    print(f"[face]   Local bot  : http://localhost:8080/?ws=ws://localhost:{_WS_GATEWAY_PORT}/face", flush=True)
    print("=" * 70 + "\n", flush=True)

    # Email the operator the per-run visualiser link so it can be opened/presented
    # without scraping ECS logs. Sent in a background thread so the SMTP round-trip
    # doesn't sit on the critical path before the bot is created and joins the call.
    # Best-effort: never let an email failure (or missing SMTP config) abort the run.
    def _send_face_link_email():
        try:
            from notify import send_face_link_email
            student_name = ""
            try:
                student_name = get_student(_cfg)["name"]
            except Exception:
                pass
            send_face_link_email(
                to="m.i.findlow@gmail.com",
                face_url=f"http://localhost:8080/?ws={face_ws_url}",
                student_name=student_name,
                interview_id=interview_id,
            )
        except Exception as e:
            print(f"[face] Could not email visualiser link: {e}", flush=True)

    threading.Thread(target=_send_face_link_email, daemon=True).start()

    # ── 2. Create bot (gives us bot_id immediately) ────────────────────────────
    from config import cfg, get_audio_settings
    import os

    audio_cfg = get_audio_settings(cfg)
    provider_name = audio_cfg.get("transcript_provider", "meeting_captions")
    key_env = audio_cfg.get("transcript_api_key_env", "")
    api_key = os.environ.get(key_env, "") if key_env else ""

    if provider_name == "meeting_captions":
        transcript_provider = {"meeting_captions": {}}
    else:
        if not api_key:
            print(f"[zoom] Warning: transcript_provider={provider_name!r} but {key_env!r} is not set in .env — falling back to meeting_captions", flush=True)
            transcript_provider = {"meeting_captions": {}}
        else:
            transcript_provider = {provider_name: {"api_key": api_key}}
            print(f"[zoom] Transcript provider: {provider_name}", flush=True)

    print(f"[zoom] Creating recall.ai bot for: {zoom_url}", flush=True)
    bot_info = client.create_bot(
        zoom_url,
        bot_name=bot_name,
        transcript_provider=transcript_provider,
        audio_ws_url=audio_ws_url,
    )
    bot_id = bot_info["id"]
    print(f"[zoom] Bot ID: {bot_id}", flush=True)

    # ── 3. Run join-wait and full init in parallel ─────────────────────────────
    # Track results/errors from both threads via shared containers.
    join_error: list[Exception | None] = [None]
    init_error: list[Exception | None] = [None]
    interview_bot_holder: list = [None]
    bridge_holder: list = [None]

    def _wait_track():
        try:
            client.wait_for_join(bot_id)
            print("[zoom] Bot is live — ready to start.", flush=True)
        except Exception as exc:
            join_error[0] = exc

    def _init_track():
        try:
            import os
            from elevenlabs import ElevenLabs
            import audio
            import bot as interview_bot_module

            voice_id = audio_cfg.get("elevenlabs_voice_id", "Rachel")
            model_id = audio_cfg.get("elevenlabs_model", "eleven_turbo_v2_5")
            silence_secs = audio_cfg.get("silence_duration_seconds", 4.0)

            print("[zoom] Initialising ElevenLabs TTS client...", flush=True)
            el_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

            bridge = audio_bridge.RecallAudioBridge(
                bot_id=bot_id,
                recall_client=client,
                el_client=el_client,
                voice_id=voice_id,
                model_id=model_id,
                bot_name=bot_name,
                silence_secs=silence_secs,
            )
            audio_bridge.set_bridge(bridge)

            # Monkeypatch interview_bot/audio.py so bot.py uses recall.ai I/O.
            audio.text_to_speech = audio_bridge.text_to_speech
            audio.speech_to_text = audio_bridge.speech_to_text
            audio.set_interview_start = audio_bridge.set_interview_start
            audio.prefetch_tts = audio_bridge.prefetch_tts

            interview_bot = interview_bot_module.InterviewBot()

            # LLM prefetch runs internally in parallel threads; TTS prefetch is sequential.
            # Pre-load Whisper into memory now (model file is on disk from build)
            # so it's ready before the student's first response.
            print("[zoom] Pre-loading Whisper STT model...", flush=True)
            audio._get_stt()

            print("[zoom] Prefetching LLM responses and generating TTS...", flush=True)
            interview_bot.prefetch_all()
            n_q = len(interview_bot._question_text_cache)
            for i, text in sorted(interview_bot._question_text_cache.items()):
                bridge.prefetch(text, label=f"question {i + 1}/{n_q}")
            phrase_labels = {
                "closing": "closing statement (time up)",
                "closing_complete": "closing statement (complete)",
                "open_floor": "open floor prompt",
            }
            for key, text in interview_bot._phrase_cache.items():
                bridge.prefetch(text, label=phrase_labels.get(key, key))

            bridge_holder[0] = bridge
            interview_bot_holder[0] = interview_bot
            print("[zoom] Init complete — all TTS pre-generated.", flush=True)
        except Exception as exc:
            init_error[0] = exc

    join_thread = threading.Thread(target=_wait_track, daemon=True)
    init_thread = threading.Thread(target=_init_track, daemon=True)
    join_thread.start()
    init_thread.start()

    join_thread.join()
    init_thread.join()

    if join_error[0]:
        face_channel.set_state("failed")
        raise join_error[0]
    if init_error[0]:
        face_channel.set_state("failed")
        raise init_error[0]

    # Both tracks are done: the bot is live in the call and all TTS is pre-generated.
    # This is the real "ready" moment — tell the API so the student's loading screen
    # can reveal the join button immediately instead of guessing a fixed wait.
    if interview_id is not None:
        db_client.mark_ready(interview_id)
        print(f"[zoom] Interview {interview_id} marked READY.", flush=True)

    try:
        time.sleep(2)  # brief settle so Zoom audio is stable before speaking

        # ── 4. Run the interview ───────────────────────────────────────────────
        print("[zoom] Starting interview.\n", flush=True)
        try:
            interview_bot_holder[0].run()
            status = "COMPLETED"
            face_channel.set_state("completed")
        except BaseException:
            status = "FAILED"
            face_channel.set_state("failed")
            raise
        finally:
            transcript_entries = interview_bot_holder[0].ctx.transcript if interview_bot_holder[0] is not None else []
            _print_transcript(transcript_entries)
            if interview_id is not None:
                _finish(interview_id, status, _format_transcript(transcript_entries))

    finally:
        print("\n[zoom] Leaving the call...", flush=True)
        try:
            client.leave_call(bot_id)
            print("[zoom] Bot left the meeting.", flush=True)
        except Exception as exc:
            print(f"[zoom] Warning: could not leave call cleanly: {exc}", flush=True)


def _print_transcript(transcript: list) -> None:
    from transcript_format import format_transcript
    print("\n" + "=" * 60)
    print("INTERVIEW TRANSCRIPT")
    print("=" * 60)
    print()
    print(format_transcript(transcript))
    print("=" * 60)
