"""
face_sim.py — Drive the bot-face channel with a fake interview, no external services.

Starts the same face_channel WebSocket server the real bot uses (port 8767) and
plays a scripted interview through it: state changes, bot lines, partial + final
student answers. Use it to eyeball the visualisation page (layout, colours, pulse,
captions, reconnect) without Zoom / recall.ai / ElevenLabs / OpenAI.

Usage:
    python zoom_integration/face_sim.py           # loop forever (good for leaving open)
    python zoom_integration/face_sim.py --once     # play one pass then idle

Then open the page (served separately) at http://localhost:8080/
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import face_channel

FACE_PORT = 8767

# (kind, value, hold_seconds). kind: state | bot | student | student_partial
SCRIPT = [
    ("state", "ready", 3),
    ("bot", "Hello Ada, say 'ready to begin' whenever you're ready to start.", 0),
    ("state", "speaking", 3.5),
    ("state", "listening", 1.5),
    ("student_partial", "ready to", 0.6),
    ("student", "Ready to begin.", 2),
    ("bot", "Tell me about how recursion works and when you'd reach for it.", 0),
    ("state", "speaking", 4),
    ("state", "listening", 1.5),
    ("student_partial", "recursion is when a function calls", 0.8),
    ("student_partial", "recursion is when a function calls itself with a smaller", 0.8),
    ("student",
     "Recursion is when a function calls itself with a smaller input until it "
     "reaches a base case. It's cleaner than a loop for things like tree traversal.",
     2.5),
    ("state", "thinking", 3),
    ("bot", "Good. Can you give a concrete example where recursion is clearer than iteration?", 0),
    ("state", "speaking", 4),
    ("state", "listening", 1.5),
    ("student_partial", "walking a file system directory", 0.8),
    ("student",
     "Walking a file-system directory tree — each folder can contain folders, so "
     "recursing matches the shape of the data far better than manual stack bookkeeping.",
     3),
    ("state", "thinking", 2.5),
    ("bot", "That's a great example. That's all my questions — thanks, Ada. This concludes the interview.", 0),
    ("state", "speaking", 4),
    ("state", "ready", 2),
]


def play_once() -> None:
    face_channel.meta("Ada Lovelace")
    for kind, value, hold in SCRIPT:
        if kind == "state":
            face_channel.set_state(value)
            print(f"[sim] state → {value}", flush=True)
        elif kind == "bot":
            face_channel.bot_text(value)
            print(f"[sim] bot: {value}", flush=True)
        elif kind == "student":
            face_channel.student_text(value, partial=False)
            print(f"[sim] student: {value}", flush=True)
        elif kind == "student_partial":
            face_channel.student_text(value, partial=True)
        if hold:
            time.sleep(hold)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate an interview for the bot-face page")
    parser.add_argument("--once", action="store_true", help="Play one pass then idle")
    args = parser.parse_args()

    face_channel.start(FACE_PORT)
    print(f"[sim] Face channel on ws://localhost:{FACE_PORT} — open the page now.", flush=True)
    time.sleep(1)  # give the page a moment to connect

    try:
        if args.once:
            play_once()
            print("[sim] Done. Holding so the page stays connected (Ctrl-C to quit).", flush=True)
            while True:
                time.sleep(3600)
        else:
            while True:
                play_once()
    except KeyboardInterrupt:
        print("\n[sim] Stopped.", flush=True)


if __name__ == "__main__":
    main()
