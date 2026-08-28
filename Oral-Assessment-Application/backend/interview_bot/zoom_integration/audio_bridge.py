"""
audio_bridge.py — Drop-in replacement for interview_bot/audio.py.

Replaces local microphone/speaker I/O with recall.ai:
  - text_to_speech: ElevenLabs TTS → WAV → POST to recall.ai bot
  - speech_to_text: poll recall.ai transcript for new participant words

Module-level functions match the audio.py public API so they can be
assigned directly onto the audio module object (monkeypatching).
"""

import base64
import io
import os
import time
import wave
import av
import numpy as np
import select
import sys
from recall_client import RecallClient
import face_channel

# ── Global bridge instance (set via set_bridge before running the bot) ─────────
_bridge: "RecallAudioBridge | None" = None


def set_bridge(bridge: "RecallAudioBridge") -> None:
    global _bridge
    _bridge = bridge


# ── Public API matching audio.py ───────────────────────────────────────────────


def text_to_speech(text: str) -> None:
    if _bridge:
        _bridge.speak(text)


def speech_to_text(timeout: float | None = None) -> str:
    if _bridge:
        return _bridge.stream_listen(listen_timeout=timeout)
    return ""


def set_interview_start() -> None:
    if _bridge:
        _bridge.interview_start = time.time()


def prefetch_tts(text: str) -> None:
    if _bridge and text:
        _bridge.prefetch(text)


# ── WAV helpers ────────────────────────────────────────────────────────────────


def _to_wav_bytes(audio_data: np.ndarray, sample_rate: int) -> bytes:
    """Convert float32 numpy audio to a WAV byte string (16-bit PCM)."""
    buf = io.BytesIO()
    pcm16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())
    return buf.getvalue()


def _wav_to_mp3(wav_bytes: bytes) -> bytes:
    """Re-encode WAV bytes to MP3 bytes using PyAV (in-memory, no subprocess)."""
    in_buf = io.BytesIO(wav_bytes)
    out_buf = io.BytesIO()
    with av.open(in_buf, format="wav") as in_container:
        in_stream = in_container.streams.audio[0]
        with av.open(out_buf, mode="w", format="mp3") as out_container:
            out_stream = out_container.add_stream("mp3", rate=in_stream.rate)
            for frame in in_container.decode(in_stream):
                frame.pts = None
                for packet in out_stream.encode(frame):
                    out_container.mux(packet)
            for packet in out_stream.encode(None):
                out_container.mux(packet)
    return out_buf.getvalue()


def _wav_duration(wav_bytes: bytes) -> float:
    """Return playback duration of a WAV byte string in seconds."""
    with wave.open(io.BytesIO(wav_bytes)) as wf:
        return wf.getnframes() / wf.getframerate()


# ── Bridge class ───────────────────────────────────────────────────────────────


class RecallAudioBridge:
    """Manages TTS output and transcript-based STT for a recall.ai bot."""

    def __init__(
        self,
        bot_id: str,
        recall_client: RecallClient,
        el_client,
        voice_id: str,
        model_id: str,
        bot_name: str = "Interview Bot",
        silence_secs: float = 4.0,
        listen_timeout: float = 120.0,
    ):
        self.bot_id = bot_id
        self.client = recall_client
        self.el_client = el_client
        self.voice_id = voice_id
        self.model_id = model_id
        self.bot_name = bot_name
        self.silence_secs = silence_secs
        self.listen_timeout = listen_timeout

        self.interview_start: float | None = None
        self._mp3_cache: dict[str, tuple[bytes, float]] = (
            {}
        )  # text → (mp3_bytes, duration_secs)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _elapsed_str(self) -> str:
        if self.interview_start is None:
            return ""
        secs = int(time.time() - self.interview_start)
        return f" ({secs // 60}:{secs % 60:02d})"

    def _generate_wav(self, text: str) -> tuple[bytes, float]:
        audio_bytes = b"".join(self.el_client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format="pcm_24000",
        ))
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        wav = _to_wav_bytes(audio_data, 24_000)
        return wav, _wav_duration(wav)

    # ── Public interface ───────────────────────────────────────────────────────

    def prefetch(self, text: str, label: str = "") -> None:
        """Pre-generate TTS audio and cache the final MP3 so speak() is instant."""
        if text and text not in self._mp3_cache:
            print(f"[zoom] Pre-generating TTS: {label or 'audio'}...", flush=True)
            wav, duration = self._generate_wav(text)
            self._mp3_cache[text] = (_wav_to_mp3(wav), duration)

    def speak(self, text: str) -> None:
        """Generate TTS, send to the meeting bot, wait for playback to finish."""
        if not text:
            return

        print(f"\n   [Interviewer]{self._elapsed_str()}", flush=True)
        print(f"   {text}", flush=True)

        # Drive the bot-face visualisation: show the line + start the speaking pulse.
        # State is intentionally left as "speaking" on return — the next hook
        # (listen → "listening", follow-up → "thinking") sets the following state,
        # so the pulse runs for exactly the speaking window.
        face_channel.bot_text(text)
        face_channel.set_state("speaking")

        if text in self._mp3_cache:
            mp3, duration = self._mp3_cache.pop(text)
        else:
            wav, duration = self._generate_wav(text)
            mp3 = _wav_to_mp3(wav)

        self.client.output_audio(self.bot_id, base64.b64encode(mp3).decode("ascii"))

        # Wait for playback to finish before listening for a response.
        time.sleep(duration + 1.5)

    def stream_listen(self, listen_timeout: float | None = None) -> str:
        """Listen via recall.ai's per-participant raw audio stream.

        Mirrors audio.speech_to_text() exactly — same RMS VAD, same silence
        threshold, same Whisper transcription — but reads PCM from the recall.ai
        audio websocket instead of a local microphone.
        """
        import shutil
        import threading
        import audio_ws_server
        import audio as audio_module
        from config import cfg, get_audio_settings

        _STT_SAMPLE_RATE = 16_000
        _CHUNK_DURATION = 0.1

        audio_cfg = get_audio_settings(cfg)
        threshold = audio_cfg.get("silence_threshold", 0.01)
        silence_secs = audio_cfg.get("silence_duration_seconds", 4.0)

        model = audio_module._get_stt()
        chunk_samples = int(_STT_SAMPLE_RATE * _CHUNK_DURATION)
        bot_name_lower = self.bot_name.lower()

        # Drain audio that arrived during TTS playback
        q = audio_ws_server.get_queue()
        while not q.empty():
            try:
                q.get_nowait()
            except Exception:
                break

        face_channel.set_state("listening")
        print("\n[Listening… speak now, or press Enter to stop early]\n", flush=True)

        # ── In-place display (mirrors audio.py) ───────────────────────────────
        display_lines = [0]
        display_lock = threading.Lock()

        def _reprint(text: str) -> None:
            cols = shutil.get_terminal_size().columns
            with display_lock:
                if display_lines[0] > 0:
                    print("\r\033[2K", end="")
                    for _ in range(display_lines[0] - 1):
                        print("\033[A\r\033[2K", end="")
                print(text, end="", flush=True)
                display_lines[0] = max(1, (len(text) + cols - 1) // cols)

        print(f"    [You]{self._elapsed_str()}", flush=True)
        _reprint("")

        recording_done = threading.Event()
        chunks: list = []
        chunks_lock = threading.Lock()

        def _live_transcribe():
            last_seen = 0
            while not recording_done.is_set():
                time.sleep(1.0)
                with chunks_lock:
                    current = list(chunks)
                if len(current) <= last_seen:
                    continue
                last_seen = len(current)
                audio_data = np.concatenate(current, axis=0).flatten()
                segments, _ = model.transcribe(audio_data, language="en")
                partial = " ".join(seg.text.strip() for seg in segments).strip()
                _reprint(partial)
                face_channel.student_text(partial, partial=True)

        # The live partial-transcript loop re-transcribes the entire growing
        # utterance every second purely to animate the terminal. It's a heavy CPU
        # hog that, on a constrained Fargate task, starves the websocket consumer
        # and the VAD loop (causing the 15–60s lag + erratic silence detection).
        # It has zero value on ECS (no terminal), so run it only off-ECS.
        # `LIVE_TRANSCRIBE=0/1` forces the behaviour explicitly if ever needed.
        _on_ecs = bool(os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
                       or os.environ.get("ECS_CONTAINER_METADATA_URI"))
        _override = os.environ.get("LIVE_TRANSCRIBE")
        run_live = (_override == "1") if _override is not None else (not _on_ecs)

        transcribe_thread = None
        if run_live:
            transcribe_thread = threading.Thread(target=_live_transcribe, daemon=True)
            transcribe_thread.start()

        speech_started = False
        last_speech_time: float | None = None
        pending = np.array([], dtype=np.float32)
        done = False
        listen_start = time.time()
        _timeout = listen_timeout if listen_timeout is not None else self.listen_timeout

        while not done and time.time() - listen_start < _timeout:
            if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                break

            try:
                pcm, participant_name = q.get(timeout=_CHUNK_DURATION)
            except Exception:
                # No audio arrived — check wall-clock silence if speech has started
                if speech_started and last_speech_time is not None:
                    if time.time() - last_speech_time >= silence_secs:
                        done = True
                continue

            if participant_name.lower() == bot_name_lower:
                continue

            # Accumulate into fixed-size chunks for consistent VAD
            pending = np.concatenate([pending, pcm])
            while len(pending) >= chunk_samples and not done:
                chunk = pending[:chunk_samples]
                pending = pending[chunk_samples:]
                rms = float(np.sqrt(np.mean(chunk**2)))

                if not speech_started:
                    if rms > threshold:
                        speech_started = True
                        last_speech_time = time.time()
                        with chunks_lock:
                            chunks.append(chunk)
                else:
                    with chunks_lock:
                        chunks.append(chunk)
                    if rms > threshold:
                        last_speech_time = time.time()
                    elif last_speech_time is not None:
                        if time.time() - last_speech_time >= silence_secs:
                            done = True

        recording_done.set()
        if transcribe_thread is not None:
            transcribe_thread.join(timeout=10.0)

        with chunks_lock:
            final_chunks = list(chunks)

        if not final_chunks:
            print()
            face_channel.student_text("", partial=False)
            return ""

        audio_data = np.concatenate(final_chunks, axis=0).flatten()
        segments, _ = model.transcribe(audio_data, language="en")
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
        _reprint(transcript)
        print()
        face_channel.student_text(transcript, partial=False)
        return transcript
