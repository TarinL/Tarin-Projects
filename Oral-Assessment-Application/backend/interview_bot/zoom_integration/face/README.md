# Bot-face visualisation

A live "face" for the interview bot: an animated orb that shows the bot's state
(ready / listening / thinking / speaking), prints the current bot line and the
student's response, recolours per state, and pulses while the bot speaks.

It's a **static page** that renders locally in your browser and subscribes to a
WebSocket "face channel" exposed by the running bot. Because rendering is local,
it's pixel-perfect and 60fps regardless of where the bot runs; only tiny JSON
events cross the network.

## How it connects

The bot serves one WebSocket gateway (in `session.py`) behind a single ngrok
tunnel, routed by path:

- `/audio` → recall.ai per-participant PCM stream
- `/face`  → this page's state/text events

Open the page with `?ws=<face-channel-url>`. The page auto-reconnects and the
server replays the latest snapshot on connect, so order/refresh never matters.

## Serve the page

```bash
# from the repo root
python -m http.server 8080 --directory backend/interview_bot/zoom_integration/face
```

(There's also a `bot-face` config in `.claude/launch.json`.)

## A) Page-only test — no Zoom/recall/keys

```bash
cd backend/interview_bot
python zoom_integration/face_sim.py        # plays a scripted interview on :8767
# open http://localhost:8080/?ws=ws://localhost:8767
```

## B) Real LOCAL interview

```bash
cd backend/interview_bot
python zoom_integration/trigger.py --now
# the console prints the exact URLs; for a local bot use:
# http://localhost:8080/?ws=ws://localhost:8766/face   (no ngrok, lowest latency)
```

## C) Remote interview on ECS, viewed locally

The bot runs entirely on ECS (real Zoom/recall); you watch the orb on your
laptop. The bot opens an ngrok tunnel and logs the URL to CloudWatch.

1. Build & push the image (see the chat steps / repo deploy notes).
2. Start the interview the normal way (website → .NET API → ECS RunTask).
3. Grab the face URL from the log line `[face]   Remote/ECS : http://localhost:8080/?ws=wss://…/face`:
   ```bash
   aws logs tail /ecs/interview-bot --region ap-southeast-2 --follow --since 2m | grep "Remote/ECS"
   ```
4. Open that URL locally (with the page server from above running).

Note: live word-by-word student captions are disabled on ECS (CPU guard in
`audio_bridge.py`); you still get every bot line, state change, and the final
student answer. Force with `LIVE_TRANSCRIBE=1` only if you bump task CPU.
