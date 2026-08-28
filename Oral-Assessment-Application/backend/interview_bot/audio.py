"""
audio.py — TTS and STT for the interview bot.

TTS: ElevenLabs API  (pip install elevenlabs)
     Requires ELEVENLABS_API_KEY in environment.

STT: faster-whisper  (pip install faster-whisper sounddevice)
     Default model: base.en  (~150 MB, downloads on first use).
     Uses int8 quantisation for fast CPU inference.

System requirement: PortAudio
     macOS:   brew install portaudio
     Debian:  sudo apt install libportaudio2
     Windows: included with sounddevice wheel
"""

import os
import select
import shutil
import sys
import threading
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import cfg, get_audio_settings

# ── Sample rates ───────────────────────────────────────────────────────────────
_TTS_SAMPLE_RATE = 24_000  # ElevenLabs pcm_24000 native rate
_STT_SAMPLE_RATE = 16_000  # Whisper input rate
_CHUNK_DURATION = 0.1  # seconds per recording chunk

# ── Lazy-loaded singletons ─────────────────────────────────────────────────────
_elevenlabs_client = None
_stt_model: WhisperModel | None = None

# ── TTS audio cache ───────────────────────────────────────────────────────────
_audio_cache: dict[str, tuple[np.ndarray, int]] = {}


def prefetch_tts(text: str) -> None:
    """Pre-generate and cache TTS audio so playback is instant."""
    if not text or text in _audio_cache:
        return
    print(f"[audio] Pre-generating audio for: {text[:60]}{'…' if len(text) > 60 else ''}", flush=True)
    audio_data, sample_rate = _synthesize(text)
    _audio_cache[text] = (audio_data, sample_rate)


# ── Interview clock ────────────────────────────────────────────────────────────
_interview_start: float | None = None


def set_interview_start() -> None:
    global _interview_start
    _interview_start = time.time()


def _elapsed_str() -> str:
    if _interview_start is None:
        return ""
    secs = int(time.time() - _interview_start)
    return f" ({secs // 60}:{secs % 60:02d})"


def _get_elevenlabs():
    global _elevenlabs_client
    if _elevenlabs_client is None:
        from elevenlabs import ElevenLabs
        _elevenlabs_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    return _elevenlabs_client


def _synthesize(text: str) -> tuple[np.ndarray, int]:
    """Call ElevenLabs and return (float32 audio array, sample_rate)."""
    audio_cfg = get_audio_settings(cfg)
    voice_id = audio_cfg.get("elevenlabs_voice_id", "Rachel")
    model_id = audio_cfg.get("elevenlabs_model", "eleven_turbo_v2_5")
    audio_bytes = b"".join(_get_elevenlabs().text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format="pcm_24000",
    ))
    audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return audio_data, 24_000


def _get_stt() -> WhisperModel:
    global _stt_model
    if _stt_model is None:
        audio_cfg = get_audio_settings(cfg)
        model_name = audio_cfg.get("stt_model", "base.en")
        device = audio_cfg.get("stt_device", "cpu")
        # Pin ctranslate2 intra-op threads. Default 0 = auto (uses all cores —
        # correct for local/unconstrained). On ECS Fargate the container sees the
        # host's full core count but only gets its vCPU quota, so auto causes
        # thread oversubscription/thrash; the task def sets WHISPER_CPU_THREADS to
        # the provisioned vCPU count to prevent that.
        cpu_threads = int(os.environ.get("WHISPER_CPU_THREADS", "0") or 0)
        print(f"[audio] Loading Whisper model '{model_name}' on {device} (cpu_threads={cpu_threads})…", flush=True)
        _stt_model = WhisperModel(model_name, device=device, compute_type="int8", cpu_threads=cpu_threads)
    return _stt_model


# ── Public interface ───────────────────────────────────────────────────────────


def text_to_speech(text: str) -> None:
    """Synthesise *text*, stream words to the terminal as they are spoken."""
    if not text:
        return
    if text in _audio_cache:
        audio_data, sample_rate = _audio_cache.pop(text)
    else:
        audio_data, sample_rate = _synthesize(text)

    pad_seconds = 0.75
    padding = np.zeros(int(sample_rate * pad_seconds), dtype=audio_data.dtype)
    audio_data = np.concatenate([padding, audio_data])

    speech_duration = len(audio_data) / sample_rate - pad_seconds
    words = text.split()

    def _stream_words():
        print(f"\n   [Interviewer]{_elapsed_str()}\n", end="", flush=True)
        if not words:
            print()
            return
        time.sleep(pad_seconds)
        word_delay = speech_duration / len(words)
        for word in words:
            print(word, end=" ", flush=True)
            time.sleep(word_delay)
        print()

    word_thread = threading.Thread(target=_stream_words, daemon=True)
    word_thread.start()
    sd.play(audio_data, samplerate=sample_rate, blocking=True)
    word_thread.join()


def speech_to_text(timeout: float | None = None) -> str:
    """Record from the default microphone until silence or Enter, then transcribe.

    Runs a background thread that periodically transcribes accumulated audio and
    updates the [You] line in place so the transcript grows as the user speaks.

    timeout: if set, return "" after this many seconds if no speech has started.
    """
    audio_cfg = get_audio_settings(cfg)
    threshold = audio_cfg.get("silence_threshold", 0.01)
    silence_secs = audio_cfg.get("silence_duration_seconds", 4.0)

    model = _get_stt()
    chunk_size = int(_STT_SAMPLE_RATE * _CHUNK_DURATION)
    max_silent = int(silence_secs / _CHUNK_DURATION)

    print("\n[Listening… speak now, or press Enter to stop early]\n", flush=True)

    # ── In-place display helpers ───────────────────────────────────────────────
    # [You] header is printed once and stays; only the transcript line is rewritten.
    display_lines = [0]  # visual lines occupied by the transcript line
    display_lock = threading.Lock()

    def _reprint(text: str) -> None:
        cols = shutil.get_terminal_size().columns
        with display_lock:
            if display_lines[0] > 0:
                print("\r\033[2K", end="")  # clear current line
                for _ in range(display_lines[0] - 1):
                    print("\033[A\r\033[2K", end="")  # move up + clear
            print(text, end="", flush=True)
            display_lines[0] = max(1, (len(text) + cols - 1) // cols)

    print(f"    [You]{_elapsed_str()}", flush=True)
    _reprint("")

    recording_done = threading.Event()
    chunks: list[np.ndarray] = []
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

    transcribe_thread = threading.Thread(target=_live_transcribe, daemon=True)
    transcribe_thread.start()

    silence_count = 0
    speech_started = False
    listen_start = time.time()

    with sd.InputStream(
        samplerate=_STT_SAMPLE_RATE, channels=1, dtype="float32"
    ) as stream:
        while True:
            # Non-blocking check for Enter key — avoids orphaned input() threads
            if select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                break

            # Wall-clock timeout: give up waiting if no speech starts in time
            if timeout is not None and not speech_started:
                if time.time() - listen_start >= timeout:
                    break

            data, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(data**2)))

            if not speech_started:
                if rms > threshold:
                    speech_started = True
                    with chunks_lock:
                        chunks.append(data.copy())
            else:
                with chunks_lock:
                    chunks.append(data.copy())
                if rms < threshold:
                    silence_count += 1
                    if silence_count >= max_silent:
                        break
                else:
                    silence_count = 0

    recording_done.set()
    transcribe_thread.join(timeout=10.0)

    with chunks_lock:
        final_chunks = list(chunks)

    if not final_chunks:
        print()
        return ""

    # Final accurate transcription replaces the last partial
    audio_data = np.concatenate(final_chunks, axis=0).flatten()
    segments, _ = model.transcribe(audio_data, language="en")
    transcript = " ".join(seg.text.strip() for seg in segments).strip()
    _reprint(transcript)
    print()
    return transcript
