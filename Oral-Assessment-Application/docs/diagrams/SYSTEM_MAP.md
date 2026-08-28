# System Map — all services & the calls between them

A single non-temporal overview of every service in the project and what calls what.
Pairs with `INTERVIEW_BOT_FLOWCHART.md` (which shows the *sequence* of one interview);
this map shows the *static topology*.

---

## Condensed (one-page) version

Same topology, collapsed to ~15 boxes: the API's facets merged into one node, the
AWS plumbing (ECR + Secrets Manager + CloudWatch) folded into a single box, subgraph
containers dropped, and labels trimmed. Colour still carries the grouping.

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef aws  fill:#ede9fe,stroke:#7c3aed,color:#2e1065;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    CLIENT["🟦 Instructor / Student<br/>React SPA"]:::ours
    CF["🟪 CloudFront + S3<br/>(SPA + /api proxy)"]:::aws
    COG["🟪 Cognito<br/>(Teachers + Students)"]:::aws
    API["🟦 .NET API (EC2)<br/>REST · AssessmentGenerator · ECS trigger"]:::ours
    DB["🟩 RDS MySQL"]:::db
    ECS["🟪 ECS Fargate<br/>interview-bot task"]:::aws
    INFRA["🟪 ECR · Secrets Mgr · CloudWatch"]:::aws
    BOT["🟦 Python bot<br/>(+ faster-whisper STT)"]:::ours
    FACE["🟦 Bot-face viewer<br/>(optional local page)"]:::ours
    AI["🟧 OpenAI"]:::ext
    ZOOM["🟧 Zoom"]:::ext
    RECALL["🟧 recall.ai"]:::ext
    NGROK["🟧 ngrok"]:::ext
    EL["🟧 ElevenLabs"]:::ext
    SMTP["🟧 Gmail SMTP"]:::ext

    CLIENT -->|HTTPS| CF --> API
    CLIENT -->|REST| API
    CLIENT -. login .-> COG
    API -->|SQL| DB
    API -->|KB gen| AI
    API -->|RunTask| ECS
    ECS --> INFRA
    ECS -->|runs| BOT
    BOT -->|DB via API| API
    BOT --> AI
    BOT --> ZOOM
    BOT --> RECALL
    BOT --> EL
    BOT -->|"email (optional)"| SMTP
    RECALL -->|PCM| NGROK --> BOT
    BOT -->|/face| NGROK
    NGROK -. "/face" .-> FACE
    RECALL <-->|call| ZOOM
    CLIENT -->|join| ZOOM
```

If it's still slightly wide for a portrait page, change the first line to
`flowchart TB` (taller/narrower) or add
`%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%` above it for tighter packing.

---

## Condensed — emoji-free

Identical nodes and links to the condensed map above, with the emoji removed so it
renders cleanly with `htmlLabels: false` (and in any monochrome-emoji renderer). The
box **colour** still encodes the type — blue = our code, green = our DB, purple = AWS
managed, orange = external paid SaaS.

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef aws  fill:#ede9fe,stroke:#7c3aed,color:#2e1065;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    CLIENT["Instructor / Student<br/>React SPA"]:::ours
    CF["CloudFront + S3<br/>(SPA + /api proxy)"]:::aws
    COG["Cognito<br/>(Teachers + Students)"]:::aws
    API[".NET API (EC2)<br/>REST · AssessmentGenerator · ECS trigger"]:::ours
    DB["RDS MySQL"]:::db
    ECS["ECS Fargate<br/>interview-bot task"]:::aws
    INFRA["ECR · Secrets Mgr · CloudWatch"]:::aws
    BOT["Python bot<br/>(+ faster-whisper STT)"]:::ours
    FACE["Bot-face viewer<br/>(optional local page)"]:::ours
    AI["OpenAI"]:::ext
    ZOOM["Zoom"]:::ext
    RECALL["recall.ai"]:::ext
    NGROK["ngrok"]:::ext
    EL["ElevenLabs"]:::ext
    SMTP["Gmail SMTP"]:::ext

    CLIENT -->|HTTPS| CF --> API
    CLIENT -->|REST| API
    CLIENT -. login .-> COG
    API -->|SQL| DB
    API -->|KB gen| AI
    API -->|RunTask| ECS
    ECS --> INFRA
    ECS -->|runs| BOT
    BOT -->|DB via API| API
    BOT --> AI
    BOT --> ZOOM
    BOT --> RECALL
    BOT --> EL
    BOT -->|"email (optional)"| SMTP
    RECALL -->|PCM| NGROK --> BOT
    BOT -->|/face| NGROK
    NGROK -. "/face" .-> FACE
    RECALL <-->|call| ZOOM
    CLIENT -->|join| ZOOM
```

---

## Full-detail version

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

---

## Service inventory

| Service | Type | Role | Talks to |
|---|---|---|---|
| Instructor / Student browser | 🟦 React SPA | Dashboards (create assignments/classes, schedule & start interviews, view gradebook, read the Zoom join link) | CloudFront, Cognito, .NET API |
| Bot-face viewer | 🟦 our code (local page) | Optional live visualiser of bot state/lines over the bot's `/face` WebSocket | ngrok (bot's tunnel) |
| CloudFront `d7o47tp7r931l…` | 🟪 AWS | CDN: serves the SPA (S3 origin) and proxies `/api/*` and `/start/*` to the API; `/static/*` + default → S3 | S3, .NET API |
| S3 `test-18-may-instructordash` | 🟪 AWS | Static hosting of the built React app | — |
| Cognito pool `…_9OMhJP0FG` | 🟪 AWS | Auth; `Teachers` + `Students` groups. **Tokens not yet enforced by the API.** | Browsers, (planned) API |
| .NET 9 API (EC2 `16.176.4.41`) | 🟦 ours | REST CRUD + interview lifecycle; **AssessmentGenerator** (KB→rubric+questions); ECS `RunTask` trigger | RDS, OpenAI, ECS, Cognito (planned) |
| RDS MySQL `interviewdb` | 🟩 ours | System of record (interview, user, rubric, zoom, result, assignment, instructor, class, class_student) | .NET API only |
| ECS Fargate `interview-bots` | 🟪 AWS | Runs one `interview-bot` task (8 vCPU / 16 GB) per interview | ECR, Secrets Manager, CloudWatch |
| ECR `interview-bot` | 🟪 AWS | Docker image registry | ECS |
| Secrets Manager (8) | 🟪 AWS | Injects API keys into the task at launch | ECS |
| CloudWatch Logs | 🟪 AWS | Task stdout/stderr, 365-day retention | — |
| Python interview bot | 🟦 ours | Orchestrates the meeting: Zoom, recall.ai, TTS/STT, LLM, marking; all DB I/O via the API | .NET API, Zoom, recall.ai, ngrok, ElevenLabs, OpenAI, SMTP |
| faster-whisper | 🟦 self-hosted | STT, in-process inside the container (no external call) | — |
| OpenAI | 🟧 paid | `gpt-4o-mini` live questions/follow-ups **and** KB assessment generation; `gpt-4o` marking | .NET API (AssessmentGenerator) + bot |
| Zoom | 🟧 paid | S2S OAuth, create/end meeting; hosts the live call | bot, recall.ai, student |
| recall.ai | 🟧 paid | Headless bot that joins Zoom, plays our TTS, streams participant PCM back | bot, ngrok, Zoom |
| ngrok | 🟧 paid | Public `wss://` tunnel (one gateway, routed `/audio` + `/face`) so recall.ai and the face viewer can reach the in-container socket | bot, recall.ai, face viewer |
| ElevenLabs | 🟧 paid | Text-to-speech for the interviewer voice | bot |
| Gmail SMTP | 🟧 paid | Optionally emails the Zoom join link to the student (the link is also stored in the DB and printed to logs) | bot |

## Notes for the reader
- **OpenAI is called from two places:** the **.NET API** (`AssessmentGenerator`, for knowledge-base assignments — it turns instructor KB text into a weighted rubric + areas-of-focus questions) and the **bot** (live question phrasing, follow-ups, and marking). A dev-CLI twin of the generator lives at `backend/interview_bot/kb_generator.py` and must be kept prompt-identical.
- **All database access funnels through the .NET API** — neither the browser nor the bot opens MySQL directly.
- **The join link is always served to the frontend.** The bot writes the Zoom URL to the DB via `POST /api/zoom`, so the student dashboard can show it, and it is also printed to the bot's logs (`[trigger] Join URL: …`). The **SMTP email is optional** — mainly a convenience for headless runs; a valid student email is not required for the interview to work.
- **The bot-face viewer is optional.** It's a local static page that subscribes to the bot's `/face` WebSocket (same ngrok tunnel as the audio stream) to show live bot state/lines — see `../components/bot-face.md`.
- **The frontend currently calls the API two ways:** through CloudFront's `/api/*` behaviour *and* directly at `http://16.176.4.41:5000` (hardcoded in the components). The direct path is a cleanup item.
- **Auth is provisioned but not enforced:** users authenticate against Cognito (`Teachers` / `Students` groups) and instructors have a parallel `instructor` DB row, but the API does not yet validate JWTs — it trusts `instructor_id`/`student_id` supplied in the request.

> **Export:** rendered PNGs committed alongside (`system_map-1.png` … `system_map-3.png`, one per
> ```mermaid``` block in order). Regenerate with:
> `npx -p @mermaid-js/mermaid-cli mmdc -i SYSTEM_MAP.md -o system_map.png -w 2000 -s 4 -b transparent`
