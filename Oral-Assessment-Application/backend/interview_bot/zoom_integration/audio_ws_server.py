"""
audio_ws_server.py — WebSocket server that receives per-participant raw PCM audio
from recall.ai's audio_separate_raw realtime endpoint.

recall.ai pushes JSON messages here as participants speak:
  { "data": { "data": { "buffer": "<base64 S16LE PCM>",
                        "participant": { "name": "..." }, ... } } }

Audio format: 16-bit signed PCM little-endian, 16 kHz, mono.
"""

import asyncio
import base64
import json
import queue
import threading

import numpy as np

# Bounded so a slow consumer can never accumulate unbounded latency. ~60s of
# 0.1s frames; on overflow we drop the oldest frame (fresh audio is preferable
# to an ever-growing backlog). With adequate CPU the consumer keeps real-time
# pace and this cap is never reached.
_audio_queue: queue.Queue = queue.Queue(maxsize=600)


async def _handler(websocket):
    async for message in websocket:
        try:
            msg = json.loads(message)
            data = (msg.get("data") or {}).get("data") or {}
            buf = data.get("buffer", "")
            participant = ((data.get("participant") or {}).get("name") or "")
            if buf:
                raw = base64.b64decode(buf)
                # S16LE → float32 in [-1.0, 1.0]
                pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                try:
                    _audio_queue.put_nowait((pcm, participant))
                except queue.Full:
                    try:
                        _audio_queue.get_nowait()  # drop oldest
                    except queue.Empty:
                        pass
                    _audio_queue.put_nowait((pcm, participant))
        except Exception:
            pass


def start(port: int) -> int:
    import websockets

    async def _serve():
        async with websockets.serve(_handler, "0.0.0.0", port):
            await asyncio.Future()  # run forever

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_serve())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[audio_ws] Listening on port {port}", flush=True)
    return port


def get_queue() -> queue.Queue:
    return _audio_queue
