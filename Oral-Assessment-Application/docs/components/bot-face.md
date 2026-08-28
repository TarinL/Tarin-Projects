# Bot-face visualiser

A live "face" for the interview bot: an animated orb that shows the bot's state
(ready / listening / thinking / speaking), prints the current bot line and the student's
response, recolours per state, and pulses while the bot speaks. It is an optional
observability/demo surface — the interview runs fine without it.

Source: `backend/interview_bot/zoom_integration/face/` (the page) plus
`zoom_integration/face_channel.py` and `face_sim.py` (the server side).

## How it works

- The page (`face/index.html`) is a **static page** rendered locally in your browser. Rendering is
  local, so it's smooth (60fps) regardless of where the bot runs — only tiny JSON events cross the
  network.
- The running bot serves **one** WebSocket gateway (in `session.py`) behind a single ngrok tunnel,
  routed by path: `/audio` → recall.ai PCM stream, `/face` → this page's events.
- `face_channel.py` is the outbound broadcast hub. It mirrors `audio_ws_server.py`: a background
  asyncio thread serves the WebSocket; the rest of the app pushes events via thread-safe helpers
  (`set_state` / `bot_text` / `student_text` / `meta`). All helpers are safe no-ops until the
  server is started, so importing it from `main.py`/`test_runner.py` changes nothing.
- On connect, the server replays the latest snapshot, and the page auto-reconnects — so refresh
  and connection order never matter.

Event shapes broadcast to clients:

```
{ "type": "state",        "state": "ready"|"listening"|"thinking"|"speaking" }
{ "type": "bot_text",     "text": "<current bot line>" }
{ "type": "student_text", "text": "<response>", "partial": true|false }
{ "type": "meta",         "name": "<student name>" }
```

## How to access

You open the page yourself and point it at a face-channel URL via `?ws=<url>`.

First, serve the page (from the repo root):

```bash
python -m http.server 8080 --directory backend/interview_bot/zoom_integration/face
```

(There is also a `bot-face` config in `.claude/launch.json`.)

Then pick a scenario:

- **A) Page-only (no Zoom/recall/keys):**
  ```bash
  cd backend/interview_bot
  python zoom_integration/face_sim.py        # scripted interview on :8767
  # open http://localhost:8080/?ws=ws://localhost:8767
  ```
- **B) Real local interview:**
  ```bash
  cd backend/interview_bot
  python zoom_integration/trigger.py --now
  # the console prints the exact URLs; for a local bot use:
  # http://localhost:8080/?ws=ws://localhost:8766/face   (no ngrok, lowest latency)
  ```
- **C) Remote interview on ECS, watched locally:** start the interview the normal way
  (website → API → ECS), then grab the face URL from the CloudWatch log line:
  ```bash
  aws logs tail /ecs/interview-bot --region ap-southeast-2 --follow --since 2m \
    --profile Marcus | grep "Remote/ECS"
  ```
  Open that `wss://…/face` URL in the page server above.

Note: on ECS the task now sets `LIVE_TRANSCRIBE=1` (the task has 8 vCPU), so live word-by-word
student captions are enabled. On smaller hardware a CPU guard in `audio_bridge.py` disables them;
you still get every bot line, state change, and the final student answer.

## Secrets / config

None. The face page and channel carry no secrets — only interview UI events.
