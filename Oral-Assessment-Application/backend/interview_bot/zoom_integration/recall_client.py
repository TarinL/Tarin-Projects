"""
recall_client.py — HTTP client for the recall.ai v1 API.

Handles bot lifecycle (create, status, leave) and audio I/O
(output audio to the meeting, transcript polling for input).
"""

import os
import time

import httpx

RECALL_BASE = "https://ap-northeast-1.recall.ai/api/v1"

# Bot status codes that mean the bot is live in the call
_IN_CALL_STATES = {"in_call_not_recording", "in_call_recording"}
_TERMINAL_STATES = {"call_ended", "done", "fatal", "error"}


class RecallClient:
    def __init__(self):
        api_key = os.environ.get("RECALL_API_KEY")
        if not api_key:
            raise ValueError("RECALL_API_KEY is not set in the environment")
        print(f"[recall] Using API key: {api_key[:8]}...{api_key[-4:]}", flush=True)
        self._auth = {"Authorization": f"Token {api_key}"}

    # ── Bot lifecycle ──────────────────────────────────────────────────────────

    def create_bot(
        self,
        meeting_url: str,
        bot_name: str = "Interview Bot",
        webhook_url: str | None = None,
        transcript_provider: dict | None = None,
        audio_ws_url: str | None = None,
    ) -> dict:
        """Create a recall.ai bot and have it join the given meeting URL.

        transcript_provider: provider config dict, e.g. {"meeting_captions": {}}.
        audio_ws_url: wss:// URL of our WebSocket server to receive per-participant
          raw PCM audio (audio_separate_raw, 16kHz S16LE mono).
        """
        recording_config: dict = {
            "transcript": {
                "provider": transcript_provider or {"meeting_captions": {}}
            }
        }
        realtime_endpoints: list = []
        if webhook_url:
            realtime_endpoints.append({
                "type": "webhook",
                "url": webhook_url,
                "events": ["transcript.data"],
            })
        if audio_ws_url:
            recording_config["audio_separate_raw"] = {}
            realtime_endpoints.append({
                "type": "websocket",
                "url": audio_ws_url,
                "events": ["audio_separate_raw.data"],
            })
        if realtime_endpoints:
            recording_config["realtime_endpoints"] = realtime_endpoints

        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "recording_config": recording_config,
        }
        r = httpx.post(
            f"{RECALL_BASE}/bot/",
            json=payload,
            headers=self._auth,
            timeout=30,
        )
        if not r.is_success:
            print(f"[recall] Error response: {r.text}", flush=True)
        r.raise_for_status()
        return r.json()

    def get_bot(self, bot_id: str) -> dict:
        r = httpx.get(f"{RECALL_BASE}/bot/{bot_id}/", headers=self._auth, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_status(self, bot_id: str) -> str:
        """Return the latest status code string for the bot."""
        bot = self.get_bot(bot_id)
        # recall.ai returns status_changes as a list; latest is last
        changes = bot.get("status_changes") or []
        if changes:
            return changes[-1].get("code", "unknown")
        # Fallback for alternate response shapes
        status = bot.get("status", {})
        if isinstance(status, dict):
            return status.get("code", "unknown")
        return str(status)

    def wait_for_join(self, bot_id: str, timeout: int = 180) -> None:
        """Block until the bot is recording in the call (transcription active)."""
        deadline = time.time() + timeout
        print("[recall] Waiting for bot to join the meeting...", flush=True)
        while time.time() < deadline:
            status = self.get_status(bot_id)
            print(f"[recall] Bot status: {status}", flush=True)
            if status == "in_call_recording":
                print("[recall] Bot is in the meeting.", flush=True)
                return
            if status in _TERMINAL_STATES:
                raise RuntimeError(f"Bot ended before joining: status={status!r}")
            # Poll tightly so we react the moment recall flips to recording — the
            # join/record handshake itself is recall/Zoom-side latency we can't cut,
            # but we shouldn't add up to 5s of our own waiting on top of it.
            time.sleep(2)
        raise TimeoutError(f"Bot did not join within {timeout}s")

    def wait_for_participant(
        self, bot_id: str, bot_name: str, timeout: int = 600
    ) -> None:
        """Block until at least one non-bot participant is in the call."""
        deadline = time.time() + timeout
        print("[recall] Waiting for student to join the meeting...", flush=True)
        while time.time() < deadline:
            bot = self.get_bot(bot_id)
            participants = bot.get("meeting_participants") or []
            non_bot = [
                p for p in participants
                if p.get("name", "").lower() != bot_name.lower()
            ]
            if non_bot:
                names = [p.get("name", "unknown") for p in non_bot]
                print(f"[recall] Participant(s) joined: {names}", flush=True)
                return
            time.sleep(5)
        print("[recall] Timed out waiting for participant — proceeding anyway.", flush=True)

    def leave_call(self, bot_id: str) -> None:
        r = httpx.post(
            f"{RECALL_BASE}/bot/{bot_id}/leave_call/",
            headers=self._auth,
            timeout=10,
        )
        r.raise_for_status()

    # ── Audio output ───────────────────────────────────────────────────────────

    def output_audio(self, bot_id: str, b64_mp3: str) -> None:
        """Send base64-encoded MP3 to the bot so it plays it in the meeting."""
        r = httpx.post(
            f"{RECALL_BASE}/bot/{bot_id}/output_audio/",
            json={"kind": "mp3", "b64_data": b64_mp3},
            headers=self._auth,
            timeout=60,
        )
        if not r.is_success:
            print(f"[recall] output_audio error: {r.text}", flush=True)
        r.raise_for_status()

    # ── Transcript polling ─────────────────────────────────────────────────────

    def _get_transcript_id(self, bot_id: str) -> str | None:
        """Look up and cache the transcript media ID for a bot."""
        if not hasattr(self, "_transcript_id_cache"):
            self._transcript_id_cache: dict[str, str] = {}
        if bot_id not in self._transcript_id_cache:
            bot = self.get_bot(bot_id)
            tid = (
                (bot.get("recordings") or [{}])[0]
                .get("media_shortcuts", {})
                .get("transcript", {})
                .get("id")
            )
            if tid:
                self._transcript_id_cache[bot_id] = tid
        return self._transcript_id_cache.get(bot_id)

    def get_transcript(self, bot_id: str) -> list:
        """Return the current transcript as a list of speaker segments."""
        transcript_id = self._get_transcript_id(bot_id)
        if not transcript_id:
            return []
        r = httpx.get(
            f"{RECALL_BASE}/transcript/{transcript_id}/",
            headers=self._auth,
            timeout=10,
        )
        if not r.is_success:
            print(f"[recall] transcript error body: {r.text}", flush=True)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data if isinstance(data, list) else []
