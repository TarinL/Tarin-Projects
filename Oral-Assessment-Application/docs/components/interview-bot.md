# Interview bot

The Python program that runs an interview over a real Zoom call and marks it.
Source: `backend/interview_bot/`. In production it runs as a one-shot ECS Fargate task,
launched on demand by the [API](backend-api.md).

## Current state

- **Stack:** Python 3.11 (in the container). Container entry point is
  `zoom_integration/trigger.py` (Dockerfile `ENTRYPOINT`).
- **Folder layout** (after the June 2026 tidy): core modules at the root, plus
  `zoom_integration/` (live Zoom/recall.ai path), `tests/`, `fixtures/`, `scripts/`. See the
  per-folder READMEs in those directories.

### Module map

A UML class diagram of these modules, the classes they contain, and how they call each other is
in [../diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md](../diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md).

- `config.py` — at import time, if `INTERVIEW_ID` is set, fetches the interview from the API and
  merges it onto `interview_config.json` (LLM/audio/question defaults).
- `db_client.py` — thin HTTP client for the .NET API (`get_interview`, `update_interview`,
  `create_zoom`, …). Base URL from `DB_API_BASE_URL`. The bot never touches MySQL directly.
- `zoom_integration/trigger.py` — orchestrator. Creates the Zoom meeting, writes the zoom row
  (which stores the join link for the dashboard) + interview status, prints the join link to the
  logs, optionally emails the student, optionally waits for the scheduled start, then hands off to
  `session.run_zoom_interview`. On exit, ends the Zoom meeting. The join link reaches the student
  via the dashboard and the logs regardless of whether the email succeeds — a valid student email
  is only needed to make headless runs smoother.
- `zoom_integration/zoom_client.py` — Zoom server-to-server OAuth + `create_meeting`/`end_meeting`.
- `zoom_integration/recall_client.py` — recall.ai v1 API client (`ap-northeast-1`). Spawns a bot,
  polls join status, posts MP3 audio, leaves the call.
- `zoom_integration/session.py` — per-call orchestrator. Boots one WebSocket gateway and exposes
  it via a single ngrok tunnel, routed by path: `/audio` (recall.ai per-participant PCM) and
  `/face` (the [bot-face](bot-face.md) channel). Initialises ElevenLabs TTS, monkey-patches
  `audio.text_to_speech`/`speech_to_text` onto the `RecallAudioBridge`, pre-generates LLM
  responses + TTS, then runs the interview.
- `zoom_integration/audio_ws_server.py` — decodes base64 PCM frames from recall.ai onto a
  thread-safe queue.
- `zoom_integration/audio_bridge.py` — `RecallAudioBridge`: `speak()` = ElevenLabs TTS → MP3 → POST
  to recall.ai; `stream_listen()` = PCM queue → RMS VAD → faster-whisper transcription.
- `zoom_integration/face_channel.py` / `face_sim.py` — the bot-face WebSocket channel and an
  offline simulator. See [bot-face.md](bot-face.md).
- `zoom_integration/notify.py` — SMTP (Gmail app password) emailing the meeting link.
- `bot.py` — the interview state machine (INTRO → ASK → LISTEN → FOLLOW_UP → … → CLOSE). LLM
  responses for every required question + closing scripts are prefetched in a thread pool.
- `prompts.py`, `context.py` — OpenAI prompt templates and the interview-context dataclass.
- `audio.py` — local-microphone fallback (used by `main.py` outside Zoom); the Zoom path patches
  over it at runtime.
- `marker.py` — post-interview grading. Pulls transcript + rubric from the API, asks OpenAI
  `gpt-4o` to grade, parses per-criterion scores, POSTs a `result` row.
- `scripts/` (`seed_interview.py`, `apply_to_config.py`), `tests/` (`test_runner.py`), `main.py` —
  local development helpers; not used in the ECS path.

### Models used

- **OpenAI** — `gpt-4o-mini` for live question generation, `gpt-4o` for marking.
- **recall.ai** (`ap-northeast-1`) — the headless meeting bot (plays our TTS, streams raw PCM back).
- **ElevenLabs** — TTS. Voice `fATgBRI8wg5KkDFg8vBd` (James), model `eleven_turbo_v2_5`,
  `pcm_24000` re-encoded to MP3.
- **Zoom** — server-to-server OAuth (`meeting:write:admin`, `meeting:update:status:admin`).
- **ngrok** — exposes the in-container WebSocket gateway as a public `wss://` URL for recall.ai.
- **Gmail SMTP** — sends the join link.
- **faster-whisper** (`base.en`, int8) — in-process STT, baked into the image.

### Marker is not auto-invoked in the ECS path

In the local CLI path, `main._write_back()` calls `marker.mark_interview()`. In the ECS path
(`trigger.py` → `session.run_zoom_interview()`), the marker is **not** auto-invoked today — the
frontend triggers marking, or it needs wiring into `session.py`. See
[known issues](../reference/known-issues.md).

## Container & deployment

- **Image:** `python:3.11-slim` + ffmpeg/libsndfile/libportaudio2, requirements installed, and the
  Whisper `base.en` model + the ngrok binary **pre-pulled into the image** so Fargate cold-start
  doesn't download them. Entry point `python zoom_integration/trigger.py`, default command `--now`.
  Pushed to ECR `interview-bot:latest` (~563 MB; last push 2026-06-09).
- **Task definition `interview-bot` (live revision :7, verified):** **8192 CPU / 16384 MB**
  (8 vCPU / 16 GB) — a large bump from earlier revisions to give faster-whisper enough headroom to
  run live transcription. `networkMode awsvpc`. Roles: execution `interview-bot-execution-role`,
  task `interview-bot-task-role`. Logs → CloudWatch `/ecs/interview-bot`.
- **Task env (plain):** `DB_API_BASE_URL=http://16.176.4.41:5000`, `SMTP_HOST/PORT/USER`,
  `EMAIL_FROM`, `LIVE_TRANSCRIBE=1`, and thread caps `WHISPER_CPU_THREADS=4`,
  `OMP_NUM_THREADS=4`, `OPENBLAS_NUM_THREADS=4`, `MKL_NUM_THREADS=4`.
- **Task secrets (from Secrets Manager):** 8 — see [reference/secrets.md](../reference/secrets.md).
- The repo's `task_definition.json` matches the live revision exactly.

## How to access

- **You don't call the bot directly.** It is launched by `POST /api/interview/{id}/start`. Watch
  it run via CloudWatch: `aws logs tail /ecs/interview-bot --since 5m --follow --profile Marcus`.
- **Locally (full pipeline, no ECS/API):** `cd backend/interview_bot && docker compose up --build`.
  Uses the repo-root `.env` and the bind-mounted `interview_config.json`. See
  [build/2-build-run-local.md](../build/2-build-run-local.md).
- **Offline tests / face preview:** `python tests/test_runner.py` and
  `python zoom_integration/face_sim.py` (no external services). See
  [bot-face.md](bot-face.md) and `backend/interview_bot/tests/README.md`.

## Secrets / config

The bot reads everything from environment variables (locally from the repo-root `.env`; in
production from the task definition's `secrets` + `environment`). The full per-variable map —
local `.env` name, AWS Secrets Manager name, deployed env-var name, and consumer — is in
[reference/secrets.md](../reference/secrets.md). `.env.example` at the repo root lists every
variable.
