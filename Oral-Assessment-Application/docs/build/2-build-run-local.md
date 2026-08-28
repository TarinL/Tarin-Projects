# 2. Build & run locally

How to run each component on your own machine from a cold clone. The API and database are already
deployed on AWS, so for a quick look you mainly need the frontend and (optionally) the bot.

## Prerequisites

- **Node.js 18+** and npm — frontend.
- **.NET 9 SDK** — backend API.
- **Docker Desktop** (running) — interview bot.
- **Python 3.11+** — only if you want to run the bot's offline tests / scripts outside Docker.
- A **`.env`** at the repo root with the service keys. The real `.env` is gitignored and is
  supplied with the submission; `/.env.example` lists every variable. See
  [reference/secrets.md](../reference/secrets.md).

```bash
git clone git@github.com:uoa-compsci399-s1-2026/capstone-project-s1-2026-team-10.git
# or over HTTPS:
# git clone https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-10.git
cd capstone-project-s1-2026-team-10
cp .env.example .env     # then fill in values (or drop in the supplied .env)
```

## Frontend

```bash
cd InstructorDash
npm install
npm start                # http://localhost:3000
```

By default the components call the **deployed** API (`http://16.176.4.41:5000` is hardcoded), so
the local UI works against live data immediately. To point it at a local API, change that URL in
the components (introducing an env var for it is a known cleanup item). Production build:

```bash
npm run build            # outputs static files to build/
```

## Backend API

```bash
cd backend/InterviewApi
dotnet restore
dotnet run               # Kestrel on http://localhost:5000 (and 5001)
```

- Reads `appsettings.json` for the RDS connection string and the `Ecs` config. By default it talks
  to the **live** RDS database.
- Swagger UI at `http://localhost:5000/swagger`.
- For the ECS trigger (`POST /api/interview/{id}/start`) to work locally you need AWS credentials in
  the environment — either an SSO session (`aws sso login --profile Marcus` then
  `AWS_PROFILE=Marcus dotnet run`) or AWS keys in the repo-root `.env` (loaded by
  `Config/EnvReader.cs`).

## Interview bot — full pipeline (Docker)

Runs the exact production image locally, creating a real Zoom meeting, joining via recall.ai,
conducting and writing back the interview (and emailing the student if a valid address is set —
optional; the join link is also printed to the console as `[trigger] Join URL: …`):

```bash
cd backend/interview_bot
docker compose up --build        # --build only needed the first time
```

- Uses the repo-root `.env` (`env_file: ../../.env`) and the bind-mounted `interview_config.json`.
- First run downloads the Whisper model (~150 MB) and takes a few minutes; later runs are quick.
- Edit `interview_config.json` between runs (student, assignment, rubric, questions, schedule); no
  rebuild needed. Full guide: `backend/interview_bot/README.md`.
- Results are written to whatever `DB_API_BASE_URL` points at (the deployed API by default).

## Interview bot — offline (no Zoom / recall / keys)

For a look at the interview logic and the bot-face:

```bash
cd backend/interview_bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python tests/test_runner.py --profile average     # simulated student, writes a transcript
python zoom_integration/face_sim.py               # drives the bot-face page (see bot-face.md)
```

## Verify it's working

- Frontend: the dashboard renders at `http://localhost:3000` and lists data from the live API.
- API: `curl http://localhost:5000/api/interview/1` returns JSON.
- Bot (Docker): the compose logs show the Zoom meeting being created and the bot joining.
- Bot (offline): `tests/test_runner.py` prints a full simulated interview and writes a transcript
  under `tests/test_transcripts/`.

To deploy any of these to AWS, see [build/3-build-deploy-production.md](3-build-deploy-production.md).
