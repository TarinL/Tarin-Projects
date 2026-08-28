# Backend REST API — InterviewApi

The single gateway between everything and the database, and the trigger that launches the bot.
Source: `backend/InterviewApi/`.

## Current state

- **Stack:** ASP.NET Core 9 Web API (.NET 9). Dapper for SQL, MySqlConnector, AWSSDK.ECS,
  Swashbuckle (Swagger). One controller, `Controllers/InterviewController.cs`, routed under
  `/api`.
- **Project layout** (after the June 2026 tidy):
  - `Controllers/InterviewController.cs` — all endpoints.
  - `Data/` — `DbConnectionFactory`, `IInterviewRepository`, `InterviewRepository` (parameterised
    Dapper SQL).
  - `Data/sql/` — the from-scratch schema (`000_local_full_schema.sql`) and numbered additive
    migrations, applied by hand (no migration runner).
  - `Models/` — request/response/entity records.
  - `Services/` — `AssessmentGenerator` (KB → rubric+questions via OpenAI), `AssessmentParser`.
  - `Config/EnvReader.cs` — loads a local `.env` into the process environment on boot (only if a
    `.env` is present in the working directory).
  - `Program.cs` — DI wiring, `AmazonECSClient` singleton, `DefaultTypeMap.MatchNamesWithUnderscores`.

### Endpoints (verified from the controller)

- **Interview:** `GET /api/interview/{id}` (joins interview + user + rubric + zoom + assignment),
  `GET /api/interview/studentid/{id}`, `POST /api/interview`, `PUT /api/interview/{id}`
  (bot writes status/transcript), `PATCH /api/interview/{id}/finish` (terminal status +
  transcript), `PATCH /api/interview/{id}/submission`, `POST /api/interview/{id}/result`,
  **`POST /api/interview/{id}/start` — the ECS trigger** (launches a Fargate task with
  `INTERVIEW_ID={id}`, returns `{status: "starting", interview_id: id}` immediately).
- **Assignment:** `GET/POST /api/assignment`, `PUT /api/assignment/{id}`,
  `POST /api/assignment/generate-assessment` (KB-driven generator; returns rubric+questions, does
  not persist), `POST /api/parse/rubric`, `POST /api/parse/questions`.
- **Instructor / class:** `POST /api/instructor` (9-digit id, 400 on duplicate),
  `GET /api/instructor/{id}`, `POST /api/class`, `GET /api/class/{id}`,
  `POST /api/class/{id}/students` (idempotent enrolment, returns `{added, skipped}`),
  `GET /api/class/{id}/students`, `GET /api/instructor/{id}/assignments`,
  `GET /api/instructor/{id}/interviews`, `GET /api/instructor/{id}/classes`,
  `GET /api/class/{id}/assignments`.
- **Misc CRUD:** `GET/POST /api/user`, `/api/zoom`, `/api/rubric`, `/api/result`.
- **Swagger UI** is served at `/swagger` when the app runs.

### How the trigger works

`InterviewController.StartInterview` (`POST /api/interview/{id}/start`) reads the `Ecs` section of
`appsettings.json` (cluster ARN, `SubnetIds: [subnet-0ef77772f74cadeec]`,
`SecurityGroupIds: [sg-0e03f14f32f51ab2b]`, `AssignPublicIp: ENABLED`), builds a Fargate
`RunTaskRequest`, overrides `INTERVIEW_ID` on the `interview-bot` container, and calls
`ecs.RunTaskAsync`. On the EC2 host this is authorised by the instance role
`interview-api-ec2-role`, whose inline `InterviewBotRunTask` policy grants `ecs:RunTask` +
`iam:PassRole` for the two task roles (verified live).

### Data + auth

- **Data layer:** Dapper over the RDS MySQL `interviewDb`. `MatchNamesWithUnderscores` maps MySQL
  `snake_case` to C# `PascalCase`. **No DDL foreign keys** — all relationships are enforced in
  application code. All DB I/O for the whole system funnels through this API; the bot never opens
  a MySQL connection directly. Schema detail: [database.md](database.md).
- **CORS:** open (`AllowAnyOrigin/Method/Header`).
- **Auth:** none enforced. Cognito exists and is wired into `appsettings.json`, but the controller
  trusts `instructor_id` / `student_id` from the body or route. Deriving the caller from a Cognito
  JWT is a future item.

## How to access

- **Deployed:** base URL `http://16.176.4.41:5000` (EC2), or via CloudFront at
  `https://d7o47tp7r931l.cloudfront.net/api/...` (https, recommended). Swagger:
  `http://16.176.4.41:5000/swagger`. Quick check:
  `curl http://16.176.4.41:5000/api/interview/1`.
- **Box access (ops):** **AWS SSM Session Manager** (`aws ssm start-session --target
  i-023e5be729892fe32 --profile Marcus`). There is no SSH key in the repo. The API runs as the
  `interviewapi.service` systemd unit (`User=ec2-user`, `WorkingDirectory=/home/ec2-user/interviewapi`).
- **Locally:** `cd backend/InterviewApi && dotnet run` (listens on 5000/5001). See
  [build/2-build-run-local.md](../build/2-build-run-local.md).

## Where it runs

EC2 instance `i-023e5be729892fe32` (`t3.micro`, public IP **16.176.4.41**, ap-southeast-2c).
The instance profile `interview-api-ec2-profile` (role `interview-api-ec2-role`) grants SSM
access plus `ecs:RunTask`/`iam:PassRole` and OpenAI-secret read. The box runs
**framework-dependent** publish output — the .NET 9 *runtime* is installed but **no SDK and no
source checkout**, so you build locally and copy artefacts (see
[build/3-build-deploy-production.md](../build/3-build-deploy-production.md)). The box has had
memory-pressure outages — see [known issues](../reference/known-issues.md).

## Secrets / config

- `appsettings.json` (committed) holds the **RDS connection string including the password**
  (`admin` / `BugWriters2026`). This is the one committed secret still in the repo. `OpenAI.ApiKey`
  is now empty — the API reads `OPENAI_API_KEY` from its environment (on EC2 the instance role can
  read it from Secrets Manager).
- Local runs that need AWS (for `RunTask`) use either an SSO session (`aws sso login --profile
  Marcus`) or AWS keys in a top-level `.env` loaded by `Config/EnvReader.cs`.
- Full secret map: [reference/secrets.md](../reference/secrets.md).
