"""
face_channel.py — Outbound broadcast WebSocket hub for the bot-face visualisation.

The recall.ai Output Media webpage (or a locally-served copy) connects here and
receives real-time events describing the interview: the bot's state, the line it
is currently speaking, and the student's transcribed response. The page reacts
(orb colour / pulse / text panels) accordingly.

Mirrors the structure of audio_ws_server.py: a background asyncio loop thread
serves a websockets endpoint; the rest of the app pushes events via the thread-
safe module-level helpers (set_state / bot_text / student_text / meta).

All emit helpers are safe no-ops until start() has been called, so importing this
module from main.py / test_runner.py (which never start the server) changes
nothing.

Event shapes broadcast to clients:
  { "type": "state",        "state": "ready"|"listening"|"thinking"|"speaking" }
  { "type": "bot_text",     "text": "<current bot line>" }
  { "type": "student_text", "text": "<response>", "partial": true|false }
  { "type": "meta",         "name": "<student name>" }
"""

import asyncio
import json
import threading

# ── Shared state (guarded by the asyncio loop) ─────────────────────────────────
_loop: asyncio.AbstractEventLoop | None = None
_clients: set = set()
# Last value of each event type, replayed to any client that connects later.
_snapshot: dict[str, dict] = {}
_snapshot_lock = threading.Lock()


async def _handler(websocket):
    """Register a client, replay the current snapshot, then idle until it leaves."""
    _clients.add(websocket)
    try:
        with _snapshot_lock:
            pending = list(_snapshot.values())
        for event in pending:
            await websocket.send(json.dumps(event))
        # We only push to the client; ignore anything it sends.
        async for _ in websocket:
            pass
    except Exception:
        pass
    finally:
        _clients.discard(websocket)


async def _broadcast(event: dict) -> None:
    if not _clients:
        return
    payload = json.dumps(event)
    for ws in list(_clients):
        try:
            await ws.send(payload)
        except Exception:
            _clients.discard(ws)


def attach_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Bind emit() to an externally-owned event loop.

    Used when the face _handler is served by the shared WS gateway (one ngrok
    tunnel for both /audio and /face) instead of this module's own start()."""
    global _loop
    _loop = loop


def start(port: int) -> int:
    """Start the broadcast WebSocket server on its own background loop thread.

    Standalone path (e.g. face_sim.py / pure-local testing). In a real interview
    the shared gateway in session.py serves _handler instead and calls
    attach_loop()."""
    global _loop
    import websockets

    async def _serve():
        async with websockets.serve(_handler, "0.0.0.0", port):
            await asyncio.Future()  # run forever

    def _run():
        global _loop
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _loop.run_until_complete(_serve())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[face] Listening on port {port}", flush=True)
    return port


def emit(event: dict) -> None:
    """Thread-safe broadcast of an event. No-op if the server isn't running."""
    # Cache the latest event of each type for replay to late-connecting clients.
    with _snapshot_lock:
        _snapshot[event["type"]] = event
    if _loop is None:
        return
    try:
        asyncio.run_coroutine_threadsafe(_broadcast(event), _loop)
    except Exception:
        pass


# ── Convenience helpers ────────────────────────────────────────────────────────


def set_state(state: str) -> None:
    emit({"type": "state", "state": state})


def bot_text(text: str) -> None:
    emit({"type": "bot_text", "text": text})


def student_text(text: str, partial: bool = False) -> None:
    emit({"type": "student_text", "text": text, "partial": partial})


def meta(name: str) -> None:
    emit({"type": "meta", "name": name})
