# VivāVoce — Automated AI Oral Assessment Tool

## Project Management Tool

[\[Google Drive Folder\]](https://drive.google.com/drive/folders/1g7X78B6DpObymsBLdEreB5W5cHmTgdvn?usp=sharing)

## Description

VivāVoce combats the growing unreliability of asynchronous online assessments by enabling real-time, consistent, low-cost oral assessments using LLM technology. It consists of a React web app, a REST API connecting it to a MySQL database, and a Python interview and marking bot.

Core functionality:

- Instructors create assignments of three types (Standard Interview, Assignment Review, Knowledge Review), uploading components as required.
- Instructors configure and schedule interviews for these assignments, setting due dates and durations.
- Students view their upcoming and completed interviews and trigger an upcoming interview.
- The bot starts a Zoom call, joins it, sends the student the join link, and waits for them to join before beginning.
- The bot conducts an interview of the chosen type, asking personalised questions and following up on the student's answers until time runs out or the questions are complete.
- The interview is marked against the rubric, and a suggested grade and marking report are made available to the instructor to review.

For a full write-up of the project, see the [final report](https://docs.google.com/document/d/1euMnaXFWVI9i-8_dwW6PMI7n1EaKHhi0x7bS4kE-Qdg/edit?usp=sharing).

Full documentation — architecture, per-component detail, build/deploy guides, the live AWS inventory, secrets, and diagrams — is in the [`docs/`](docs/) folder. Start at [docs/README.md](docs/README.md) or the [architecture overview](docs/ARCHITECTURE.md).

## Technologies

### Frontend (`InstructorDash`)

- JavaScript (Create React App)
- React 19
- react-router-dom 7
- axios 1
- aws-amplify 6 (Cognito sign-in)
- Deployed to AWS S3 and served through CloudFront
- Details: [docs/components/frontend.md](docs/components/frontend.md)

### Backend REST API (`backend/InterviewApi`)

- C# / ASP.NET Core 9 Web API (.NET 9)
- Dapper 2.1.72 (SQL data access)
- MySqlConnector 2.5.0
- AWSSDK.ECS 3.7
- Swashbuckle.AspNetCore 10.1.7 (Swagger)
- Runs on an AWS EC2 instance
- Details: [docs/components/backend-api.md](docs/components/backend-api.md)

### Interview / Marking Bot (`backend/interview_bot`)

- Python 3.11 (runs in Docker)
- OpenAI API (`openai` 2.31.0) — interview logic and marking
- faster-whisper 1.2.1 — speech-to-text
- ElevenLabs (`elevenlabs` >= 1.0.0) — text-to-speech
- Zoom server-to-server OAuth app — meeting creation
- recall.ai V1 API client — joining the Zoom call
- FastAPI >= 0.111 / uvicorn >= 0.29 — internal API server
- pyngrok >= 7.0 / websockets >= 12.0 — audio websocket tunnel
- Gmail SMTP — emailing join links
- Deployed as a container to an AWS ECS cluster
- Details: [docs/components/interview-bot.md](docs/components/interview-bot.md) (plus the [bot-face visualiser](docs/components/bot-face.md))

### Database

- MySQL 8.4.8
- Hosted on an AWS RDS instance
- Details: [docs/components/database.md](docs/components/database.md)

The full live AWS resource inventory is in [docs/components/aws-infrastructure.md](docs/components/aws-infrastructure.md).

## Installation and Setup

The three components run independently. The API and database are already deployed to AWS, so for local evaluation you mainly need the frontend and (optionally) the bot.

Three guides in [`docs/build/`](docs/build/) cover each path in full: [access the deployed build](docs/build/1-access-deployed.md), [build and run locally](docs/build/2-build-run-local.md), and [build and deploy to AWS](docs/build/3-build-deploy-production.md). Environment variables and secrets are documented in [docs/reference/secrets.md](docs/reference/secrets.md).

### Prerequisites

- Node.js 18+ and npm (frontend)
- .NET 9 SDK (API)
- Docker Desktop (interview bot)

### 1. Frontend

```bash
cd InstructorDash
npm install
npm start
```

The app opens at http://localhost:3000. To build for production:

```bash
npm run build
```

### 2. Backend REST API

```bash
cd backend/InterviewApi
dotnet restore
dotnet run
```

Database connection settings and AWS credentials are configured in `appsettings.json`. The Swagger UI is available at the API's `/swagger` endpoint when running.

### 3. Interview Bot

A `.env` file with the required API keys is included.

```bash
cd backend/interview_bot
docker compose up --build
```

The first run downloads the Whisper speech-to-text model (~150 MB) and takes a few minutes; later runs start in seconds. Edit `interview_config.json` to set the student, assignment, rubric, questions, and scheduling before running. See `backend/interview_bot/README.md` for the full bot guide.

## Usage Example

1. An instructor logs into the dashboard and creates an assignment (e.g. a Standard Interview), uploading any required material.
2. The instructor schedules an interview for a student, setting the duration and due date.
3. At the scheduled time the student triggers the interview; the bot creates a Zoom meeting and the join link appears on the student dashboard (it is also emailed to the student if a valid address is set).
4. The bot joins the call, conducts the personalised oral interview, and ends when time runs out or all questions are answered.
5. The bot marks the transcript against the rubric and produces a suggested grade and report for the instructor to review.

For the step-by-step request flow and per-phase diagrams, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/diagrams/INTERVIEW_BOT_FLOWCHART.md](docs/diagrams/INTERVIEW_BOT_FLOWCHART.md).

## Deployed Site

https://d7o47tp7r931l.cloudfront.net

See [docs/build/1-access-deployed.md](docs/build/1-access-deployed.md) for sign-in, account/Cognito setup, and things to be aware of.

## Future Plans

- Alpha test to gather student and instructor feedback.
- Further analysis of LLM config and prompting to improve performance.
- Support for additional video conferencing platforms beyond Zoom.
- Learning Management System (LMS) integration (e.g. Canvas) for importing classes and exporting grades.
- Expanded assignment types and richer rubric configuration.
- Instructor analytics across cohorts and assignments.
- Support for additional languages in interviews and marking.
- Support for concurrent interviews.
- Support for additional file formats beyond .txt.


## Acknowledgements

- Create React App, React, and react-router-dom documentation.
- ASP.NET Core, Dapper, and MySqlConnector documentation.
- OpenAI, ElevenLabs, faster-whisper, Zoom, recall.ai, and ngrok APIs and their documentation.
- The University of Auckland COMPSCI 399 teaching team and our project supervisor.
- Our tutor Tony for his guidance and encouragement <3
- Claude Opus + Sonnet used to assist with:
    - Planning
    - Boilerplate
    - Debugging
    - Refactoring
    - Testing scripts
    - Documentation
    - Diagrams
