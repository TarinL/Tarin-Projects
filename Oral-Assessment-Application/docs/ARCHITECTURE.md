# VivāVoce — Architecture Overview

VivāVoce is an automated AI oral-assessment tool. Instructors create assignments and
schedule interviews; a bot runs each interview over a real Zoom call (speaking and
listening in real time), then marks the transcript against a rubric. This document is the
entry point — it explains how the pieces fit together and links to the detailed docs.

**AWS region for everything:** `ap-southeast-2` (Sydney). **AWS account:** `859108043010`.
All live AWS details in these docs were verified against the running account on 2026-06-12.

---

## The five components

| Component | Lives in | What it is | Detail |
|---|---|---|---|
| Frontend (InstructorDash) | `InstructorDash/` | React web app for instructors and students | [components/frontend.md](components/frontend.md) |
| REST API (InterviewApi) | `backend/InterviewApi/` | ASP.NET Core 9 API; the single gateway to the database and the ECS trigger | [components/backend-api.md](components/backend-api.md) |
| Interview bot | `backend/interview_bot/` | Python bot that runs and marks the interview | [components/interview-bot.md](components/interview-bot.md) |
| Bot-face visualiser | `backend/interview_bot/zoom_integration/face/` | Live animated "face" page showing bot state | [components/bot-face.md](components/bot-face.md) |
| MySQL database | AWS RDS `interviewdb` | Shared data store (accessed only through the API) | [components/database.md](components/database.md) |

The live AWS resource inventory (verified) is in
[components/aws-infrastructure.md](components/aws-infrastructure.md). A UML use case diagram of
who does what (instructor, student, and the bot as a system actor) is in
[diagrams/USE_CASE_DIAGRAM.md](diagrams/USE_CASE_DIAGRAM.md).

## How a request flows

This is the full system map (the static topology — what calls what). The standalone copy,
condensed variants, and a service-by-service inventory are in
[diagrams/SYSTEM_MAP.md](diagrams/SYSTEM_MAP.md).

Legend — 🟦 our code · 🟩 our DB · 🟪 AWS managed · 🟧 external paid SaaS.
Solid arrow = live call (labelled with purpose). Dashed = auth / optional / "runs".

```mermaid
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef aws  fill:#ede9fe,stroke:#7c3aed,color:#2e1065;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    %% ───────────── Clients ─────────────
    INST["🟦 Instructor<br/>browser (React SPA)"]:::ours
    STU["🟦 Student<br/>browser (React SPA)"]:::ours
    FACE["🟦 Bot-face viewer<br/>optional local page<br/>(?ws=…/face)"]:::ours

    %% ───────────── AWS account 859108043010 · ap-southeast-2 ─────────────
    subgraph AWS["AWS · account 859108043010 · ap-southeast-2"]
        direction LR
        CF["🟪 CloudFront<br/>d7o47tp7r931l.cloudfront.net<br/>(/api·/start → API · /static·default → S3)"]:::aws
        S3["🟪 S3<br/>test-18-may-instructordash<br/>(static React build)"]:::aws
        COG["🟪 Cognito<br/>pool ap-southeast-2_9OMhJP0FG<br/>app client + Teachers/Students groups"]:::aws

        subgraph APIBOX["EC2 i-023e5be… · 16.176.4.41 · .NET 9 API (systemd interviewapi.service)"]
            direction TB
            APIR["🟦 InterviewController<br/>REST CRUD + interview lifecycle<br/>(interview · user · rubric · zoom · result ·<br/>assignment · instructor · class)"]:::ours
            AGEN["🟦 AssessmentGenerator<br/>KB text → rubric + questions<br/>(knowledge_base mode)"]:::ours
            TRIG["🟦 ECS trigger<br/>RunTask on /interview/{id}/start"]:::ours
        end

        DB["🟩 RDS MySQL · interviewdb<br/>interview · user · rubric · zoom · result ·<br/>assignment · instructor · class · class_student<br/>(no DDL FKs — enforced in app code)"]:::db

        subgraph ECSBOX["ECS Fargate · cluster interview-bots · task interview-bot (8 vCPU / 16 GB)"]
            direction TB
            BOT["🟦 Python interview bot<br/>trigger · session · bot · marker"]:::ours
            WHIS["🟦 faster-whisper STT<br/>self-hosted, baked into image"]:::ours
        end

        ECR["🟪 ECR<br/>interview-bot:latest"]:::aws
        SECM["🟪 Secrets Manager<br/>8 secrets (OpenAI, Recall, ElevenLabs,<br/>Zoom×3, SMTP, ngrok)"]:::aws
        CW["🟪 CloudWatch Logs<br/>/ecs/interview-bot"]:::aws
    end

    %% ───────────── External paid SaaS ─────────────
    subgraph EXT["External paid SaaS"]
        direction TB
        AI["🟧 OpenAI<br/>gpt-4o-mini (questions/follow-ups + KB gen)<br/>gpt-4o (marking)"]:::ext
        ZOOM["🟧 Zoom<br/>S2S OAuth + Meetings API"]:::ext
        RECALL["🟧 recall.ai<br/>headless meeting bot"]:::ext
        NGROK["🟧 ngrok<br/>public wss:// tunnel (/audio + /face)"]:::ext
        EL["🟧 ElevenLabs<br/>TTS"]:::ext
        SMTP["🟧 Gmail SMTP<br/>meeting-link email (optional)"]:::ext
    end

    %% ───────────── Edges: clients & web tier ─────────────
    INST -->|HTTPS| CF
    STU -->|HTTPS| CF
    CF -->|static assets| S3
    CF -->|"/api/* proxy"| APIR
    INST -. "login → JWT (Teachers)" .-> COG
    STU -. "login → JWT (Students)" .-> COG
    APIR -. "validate JWT (planned)" .-> COG

    %% direct REST (frontend currently also hits :5000 directly, bypassing CloudFront)
    INST -->|"REST: assignments, classes,<br/>instructors, interviews, results"| APIR
    STU -->|"REST: schedule + start interview,<br/>read join link from dashboard"| APIR
    INST -->|"KB: generate-assessment"| AGEN

    %% ───────────── Edges: API tier ─────────────
    APIR -->|Dapper SQL| DB
    AGEN -->|"KB → rubric + questions"| AI
    APIR --> TRIG
    TRIG -->|RunTask Fargate| ECSBOX

    %% ───────────── Edges: ECS lifecycle ─────────────
    ECSBOX -->|pull image| ECR
    ECSBOX -->|inject secrets → env| SECM
    BOT -->|stdout / stderr| CW

    %% ───────────── Edges: bot ↔ everything ─────────────
    BOT -->|"GET/PUT/PATCH interview,<br/>POST zoom (stores join link), POST result"| APIR
    BOT -->|"OAuth + create/end meeting"| ZOOM
    BOT -->|"create bot, output_audio, leave"| RECALL
    BOT -->|TTS audio| EL
    BOT -->|"questions, follow-ups, marking"| AI
    BOT -->|"open tunnel (/audio + /face)"| NGROK
    BOT -. "email join link (optional)" .-> SMTP
    BOT --> WHIS

    %% ───────────── Edges: live meeting + viewer ─────────────
    RECALL -->|"raw PCM over wss"| NGROK
    NGROK -->|PCM → STT| BOT
    NGROK -. "/face events" .-> FACE
    RECALL <-->|joins call| ZOOM
    STU -->|joins call| ZOOM
```

### One interview, end to end

1. **Instructor creates an assignment** in the React dashboard → `POST /api/assignment`.
2. **An interview is scheduled** → the dashboard POSTs a rubric, a placeholder zoom row, then
   the interview (`POST /api/rubric`, `/api/zoom`, `/api/interview`).
3. **The interview is triggered** → `POST /api/interview/{id}/start`. The .NET API calls
   `ecs:RunTask` to launch the bot container on Fargate with `INTERVIEW_ID={id}` and returns
   immediately (`{status: "starting"}`).
4. **The container boots** (`zoom_integration/trigger.py`): it fetches the interview from the
   API, creates a Zoom meeting, and writes the join link back to the API (so it shows on the
   student dashboard) and to the logs. It optionally emails the student the link, then waits for
   the start time.
5. **The interview runs** (`zoom_integration/session.py`): a recall.ai bot joins the Zoom call;
   the bot speaks via ElevenLabs TTS and listens via faster-whisper STT; `bot.py` drives the
   question/follow-up state machine using OpenAI; the [bot-face](components/bot-face.md) page can
   watch live.
6. **It finishes**: the transcript and final status are written back via the API; the Zoom
   meeting ends.
7. **Marking** (`marker.py`): the transcript + rubric go to OpenAI; a suggested grade and report
   are written back as a `result` row for the instructor to review at `/report/:id`.

A fuller, narrated version of this flow (with the exact endpoints and status transitions) is in
[components/backend-api.md](components/backend-api.md) and the per-phase flowchart in
[diagrams/INTERVIEW_BOT_FLOWCHART.md](diagrams/INTERVIEW_BOT_FLOWCHART.md).

## Build & run

The build instructions are split into three guides under [build/](build/):

1. [Access the deployed build](build/1-access-deployed.md) — the live site URL, accounts, and
   what to be aware of. Start here if you just want to use the running system.
2. [Build & run locally](build/2-build-run-local.md) — run each component on your own machine
   from a cold clone.
3. [Build & deploy to AWS](build/3-build-deploy-production.md) — push new versions of each
   component to the live deployment.

## Other references

- [reference/secrets.md](reference/secrets.md) — every secret, its local `.env` name, its AWS
  Secrets Manager name, and where it is consumed.
- [reference/known-issues.md](reference/known-issues.md) — the risk register.
- [diagrams/SYSTEM_MAP.md](diagrams/SYSTEM_MAP.md) — service topology diagram and inventory.
- [diagrams/USE_CASE_DIAGRAM.md](diagrams/USE_CASE_DIAGRAM.md) — UML use case diagram.
- [diagrams/DATABASE_ERD.md](diagrams/DATABASE_ERD.md) — database entity relationship diagram.
- [diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md](diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md) — UML class
  diagram of the bot's modules and classes.
- [diagrams/](diagrams/) — rendered flowcharts and the system map.
- [costing/COSTING.md](costing/COSTING.md) — the per-interview cost model.
