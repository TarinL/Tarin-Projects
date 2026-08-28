# Secrets & configuration reference

Where every secret and config value lives, in all three places it can appear:

- **Local `.env`** — at the **repo root** (`/.env`). Loaded by the bot (`main.py` etc. via
  `python-dotenv`) and by `docker-compose.yml` (`env_file: ../../.env`). The .NET API loads it
  too if present (`Config/EnvReader.cs`). A names-only template is committed at `/.env.example`.
- **AWS Secrets Manager** — region `ap-southeast-2`, account `859108043010`. Injected into the
  Fargate task by `task_definition.json`'s `secrets` block.
- **`backend/InterviewApi/appsettings.json`** — committed; holds the API's config and the RDS
  connection string.

## Interview bot — environment variables

| Purpose | Local `.env` name | AWS Secrets Manager secret | Deployed container env var | Consumed by |
|---|---|---|---|---|
| OpenAI key | `OPENAI_API_KEY` | `OPENAI_API_KEY` | `OPENAI_API_KEY` | `marker.py`, `prompts.py` |
| OpenAI model (optional) | `OPENAI_MODEL` | — | — (defaults to `gpt-4o` in marker) | `marker.py` |
| recall.ai key | `RECALL_API_KEY` | `RECALL_API_KEY` | `RECALL_API_KEY` | `recall_client.py` |
| ElevenLabs key | `ELEVENLABS_API_KEY` | `ELEVENLABS_API_KEY` | `ELEVENLABS_API_KEY` | `audio_bridge.py` |
| ngrok token | `NGROK_AUTH_TOKEN` | `NGROK_AUTHTOKEN` *(secret name)* | `NGROK_AUTH_TOKEN` | `session.py` |
| Zoom account id | `ZOOM_ACCOUNT_ID` | `ZOOM_ACCOUNT_ID` | `ZOOM_ACCOUNT_ID` | `zoom_client.py` |
| Zoom client id | `ZOOM_CLIENT_ID` | `ZOOM_CLIENT_ID` | `ZOOM_CLIENT_ID` | `zoom_client.py` |
| Zoom client secret | `ZOOM_CLIENT_SECRET` | `ZOOM_CLIENT_SECRET` | `ZOOM_CLIENT_SECRET` | `zoom_client.py` |
| SMTP password | `SMTP_PASSWORD` | `SMTP_PASSWORD` | `SMTP_PASSWORD` | `notify.py` |
| SMTP host | `SMTP_HOST` | — (plain env) | `SMTP_HOST` (`smtp.gmail.com`) | `notify.py` |
| SMTP port | `SMTP_PORT` | — (plain env) | `SMTP_PORT` (`587`) | `notify.py` |
| SMTP user | `SMTP_USER` | — (plain env) | `SMTP_USER` | `notify.py` |
| Email "from" | `EMAIL_FROM` | — (plain env) | `EMAIL_FROM` | `notify.py` |
| API base URL | `DB_API_BASE_URL` | — (plain env) | `DB_API_BASE_URL` (`http://16.176.4.41:5000`) | `db_client.py` |
| STT threads (optional) | `WHISPER_CPU_THREADS` | — (plain env) | `WHISPER_CPU_THREADS` (`4`) | `audio.py` |
| Live captions (optional) | `LIVE_TRANSCRIBE` | — (plain env) | `LIVE_TRANSCRIBE` (`1`) | `audio_bridge.py` |
| BLAS thread caps | — | — (plain env) | `OMP_/OPENBLAS_/MKL_NUM_THREADS` (`4`) | numpy/ctranslate2 |
| Interview id | — (set per run) | — | `INTERVIEW_ID` (per-task override) | `config.py` |

Notes:

- **ngrok name mismatch:** the code and the deployed container env both use `NGROK_AUTH_TOKEN`; the
  *Secrets Manager secret* is named `NGROK_AUTHTOKEN` and the task definition maps it to the
  `NGROK_AUTH_TOKEN` env var. The local `.env` must use `NGROK_AUTH_TOKEN` (it was corrected from
  `NGROK_AUTHTOKEN` in June 2026).
- `DB_API_KEY` appears in some `.env` copies but is **not read by the bot** today.
- `DEEPGRAM_API_KEY` may appear in older `.env` copies; STT uses faster-whisper, so it is unused.

## Backend API — `appsettings.json`

| Key | Holds | Secret? |
|---|---|---|
| `ConnectionStrings:Default` | RDS MySQL connection string incl. `admin` / `BugWriters2026` | **Yes — committed.** The one secret still in the repo. |
| `OpenAI:ApiKey` | empty (`""`) | API reads `OPENAI_API_KEY` from its environment instead (on EC2 the instance role can read the Secrets Manager secret). |
| `OpenAI:Model` / `OpenAI:BaseUrl` | `gpt-4o-mini` / `https://api.openai.com/v1` | No. |
| `Cognito:*` | pool `ap-southeast-2_9OMhJP0FG`, client `2rdo1hk080nq8pdame6jv3v0jp` | No (public IDs). |
| `Ecs:*` | cluster ARN, `subnet-0ef77772f74cadeec`, `sg-0e03f14f32f51ab2b`, `AssignPublicIp` | No. |

## Frontend

No secrets — only the public Cognito pool/client IDs in `InstructorDash/src/config/awsConfig.js`.

## Handling for submission

The real `.env` is gitignored and is provided to markers directly (see
[build/1-access-deployed.md](../build/1-access-deployed.md) /
[build/2-build-run-local.md](../build/2-build-run-local.md)). The committed RDS password in
`appsettings.json` is a known exposure flagged in [known-issues.md](known-issues.md); rotating it
and scrubbing history was deferred.
