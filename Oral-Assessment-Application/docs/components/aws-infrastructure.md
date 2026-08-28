# AWS infrastructure inventory

Every live AWS resource the system uses. **Region `ap-southeast-2`, account `859108043010`.**
All values below were verified against the running account on 2026-06-12 with the AWS CLI.

| Service | Resource | Notes |
|---|---|---|
| ECS | Cluster `interview-bots` | Fargate, no long-running services. Tasks launched on demand by the API's `ecs:RunTask`. |
| ECS | Task definition `interview-bot` (live revision **:7**) | **8192 CPU / 16384 MB** (8 vCPU / 16 GB), awsvpc, image `…/interview-bot:latest`. Pulls 8 secrets from Secrets Manager; sets plain env incl. `DB_API_BASE_URL`, `LIVE_TRANSCRIBE=1`, thread caps. Mirrors repo `task_definition.json`. |
| ECR | Repository `interview-bot` | Holds the bot image (~563 MB; last push 2026-06-09). |
| EC2 | `i-023e5be729892fe32` "interview-api-server" (`t3.micro`, **16.176.4.41**, ap-southeast-2c) | Runs the .NET API (`interviewapi.service`). Instance profile `interview-api-ec2-profile`. Public IP is **not** an Elastic IP. Memory-pressure history — see [known issues](../reference/known-issues.md). |
| RDS | `interviewdb` (MySQL 8.4.8, `db.t4g.micro`, 20 GB, public) | Shared DB. Endpoint `interviewdb.c2loht3fr432.ap-southeast-2.rds.amazonaws.com:3306`. See [database.md](database.md). |
| Secrets Manager | `OPENAI_API_KEY`, `RECALL_API_KEY`, `ELEVENLABS_API_KEY`, `ZOOM_ACCOUNT_ID`, `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `SMTP_PASSWORD`, `NGROK_AUTHTOKEN` | 8 secrets, injected into the Fargate task. The `NGROK_AUTHTOKEN` secret maps to container env `NGROK_AUTH_TOKEN`. See [reference/secrets.md](../reference/secrets.md). |
| IAM | `interview-bot-execution-role` | `ecs-tasks.amazonaws.com`. Attached: `AmazonECSTaskExecutionRolePolicy`, `SecretsManagerReadWrite`. Used by the ECS agent to pull the image + resolve secrets. |
| IAM | `interview-bot-task-role` | `ecs-tasks.amazonaws.com`. Attached: `CloudWatchLogsFullAccess`. Used by the container. |
| IAM | `interview-api-ec2-role` (via profile `interview-api-ec2-profile`) | Attached: `AmazonSSMManagedInstanceCore`, `AmazonSSMPatchAssociation`. Inline: `InterviewBotRunTask` (`ecs:RunTask`/`DescribeTasks`/`ListTasks` + `iam:PassRole` for the two task roles) and `InterviewApiOpenAISecretRead`. So the API host can trigger the bot and read the OpenAI secret without static keys. |
| CloudWatch Logs | `/ecs/interview-bot` | Bot logs. Stream prefix `ecs`. |
| Cognito | User pool `ap-southeast-2_9OMhJP0FG` ("User pool - akritr"), app client `2rdo1hk080nq8pdame6jv3v0jp` ("capstone-webapp"), groups `Teachers` / `Students` | Used by the frontend for sign-in. Not yet enforced by the API. |
| S3 | `test-18-may-instructordash` | Static React build. |
| CloudFront | `ESSBPX2SEQR6S` → `d7o47tp7r931l.cloudfront.net` | Origins/behaviors (verified): default + `/static/*` → S3; `/api/*` → `16.176.4.41.nip.io` (backend-api); `/start/*` → same EC2 origin (bot-api). |
| VPC | `vpc-03c095e1e9831c6dd` (default) | ECS task subnet `subnet-0ef77772f74cadeec` (public, ap-southeast-2b). EC2 in ap-southeast-2c. |
| Security groups | `interview-app-sg` (sg-0e03f14f32f51ab2b — ECS + RDS), `api-server-gp` (sg-0bb0d6bf88fa6e7ab — EC2 API) | `api-server-gp` opens 80 + 5000 to `0.0.0.0/0`; `interview-app-sg` opens 3306 to `0.0.0.0/0` (plus an admin IP). Tightening both is a hardening item. |

## Third-party / paid services

- **OpenAI** — `gpt-4o-mini` (live questions), `gpt-4o` (marking). Key in Secrets Manager.
- **recall.ai** (`ap-northeast-1`) — headless meeting bot; joins Zoom, plays TTS, streams PCM back.
- **ElevenLabs** — TTS (voice `fATgBRI8wg5KkDFg8vBd`, model `eleven_turbo_v2_5`).
- **Zoom** — server-to-server OAuth app (`meeting:write:admin`, `meeting:update:status:admin`).
- **ngrok** — exposes the in-task WebSocket gateway as a public `wss://` URL for recall.ai.
- **Gmail SMTP** — `m.i.findlow@gmail.com` (app password) sends the join link.
- **faster-whisper** (`base.en`, int8) — self-hosted STT baked into the image.

Cost model: [costing/COSTING.md](../costing/COSTING.md).

## How to access AWS

Use the AWS CLI with the SSO profile `Marcus` (account `859108043010`, region `ap-southeast-2`):

```bash
aws sso login --profile Marcus
aws sts get-caller-identity --profile Marcus       # should report account 859108043010
```

SSO start URL: `https://identitycenter.amazonaws.com/ssoins-82596a7dc8914808`. Access is granted
in IAM Identity Center, not via a static key file (see `InstructorDash/DEPLOY.md`).

## Managing Cognito users (sign-in accounts)

App sign-in is backed by the Cognito user pool **`ap-southeast-2_9OMhJP0FG`** ("User pool -
akritr"), app client `2rdo1hk080nq8pdame6jv3v0jp` ("capstone-webapp"). Users belong to one of two
groups: **`Teachers`** (instructors) or **`Students`**.

### Via the AWS Console

Sign in to account `859108043010` → **Cognito** → **User pools** → *User pool - akritr* →
**Users**. From here you can create users, reset/set passwords, confirm accounts, and add users to
groups. Groups are under the **Groups** tab.

### Via the AWS CLI

All commands use `--user-pool-id ap-southeast-2_9OMhJP0FG --profile Marcus`.

```bash
POOL=ap-southeast-2_9OMhJP0FG

# List users
aws cognito-idp list-users --user-pool-id $POOL --profile Marcus \
  --query "Users[].{user:Username,status:UserStatus}" --output table

# Create a user (suppress the invite email; set the email as verified)
aws cognito-idp admin-create-user --user-pool-id $POOL --profile Marcus \
  --username "jane@example.com" \
  --user-attributes Name=email,Value="jane@example.com" Name=email_verified,Value=true \
  --message-action SUPPRESS

# Set (or change) a user's password — --permanent skips the force-change prompt
aws cognito-idp admin-set-user-password --user-pool-id $POOL --profile Marcus \
  --username "jane@example.com" --password 'New-Strong-Passw0rd!' --permanent

# Add the user to a group (Teachers or Students)
aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --profile Marcus \
  --username "jane@example.com" --group-name Teachers

# Trigger a self-service password reset email instead of setting one directly
aws cognito-idp admin-reset-user-password --user-pool-id $POOL --profile Marcus \
  --username "jane@example.com"

# Remove a user
aws cognito-idp admin-delete-user --user-pool-id $POOL --profile Marcus \
  --username "jane@example.com"
```

### Self-service (end users)

Users can sign in and change their own password through the app's login flow
(`https://d7o47tp7r931l.cloudfront.net`); a first-time admin-created account may be prompted to set
a new password on first sign-in unless one was set with `--permanent`.

### Note: the parallel DB records

Cognito only handles authentication. For an **instructor** to own classes/assignments, the app
also expects a row in the `instructor` table (9-digit id + name) created via `POST /api/instructor`;
**students** are referenced by `student_id` in the `user` table. Creating a Cognito account alone
does not create these rows — see [database.md](database.md) and [backend-api.md](backend-api.md).

