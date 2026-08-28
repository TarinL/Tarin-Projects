# 1. Access the deployed build

Use the system that's already running on AWS. Nothing to build or install — start here if you
just want to see VivāVoce working.

## The live site

**https://d7o47tp7r931l.cloudfront.net**

This is the InstructorDash web app (React build on S3, served via CloudFront). It will stay up
until the final mark is released.

- **Sign in** uses AWS Cognito. You need an account in the Cognito user pool
  (`ap-southeast-2_9OMhJP0FG`), in either the `Teachers` or `Students` group. Accounts are
  provisioned by the team — ask for one, or use the credentials supplied with the submission. To
  create accounts, set/reset passwords, or add users to groups yourself, see
  [Managing Cognito users](../components/aws-infrastructure.md#managing-cognito-users-sign-in-accounts).
- **Instructor flow:** create an assignment → schedule an interview → it appears under
  `/instructor/interviews`; review results at `/report/:id`.
- **Student flow:** `/student/dashboard` → start an upcoming interview. The bot creates a Zoom
  meeting and the **join link appears on the student dashboard** (the bot writes it back via the
  API). The student email is optional — see the note below.

## The API

The backend is reachable directly and via CloudFront:

- Direct: `http://16.176.4.41:5000` — e.g. `curl http://16.176.4.41:5000/api/interview/1`.
- Swagger UI: `http://16.176.4.41:5000/swagger`.
- Via CloudFront (https): `https://d7o47tp7r931l.cloudfront.net/api/...`.

## Watching an interview run

When an interview is triggered, the bot runs as an ECS Fargate task and logs to CloudWatch. With
AWS access (below):

```bash
aws logs tail /ecs/interview-bot --since 5m --follow --profile Marcus
```

You can also watch the live "face" of the bot — see
[components/bot-face.md](../components/bot-face.md), scenario C.

## AWS account access (optional, for inspecting infrastructure)

- **Account:** `859108043010`, region `ap-southeast-2` (Sydney).
- Access is an **IAM Identity Center (SSO)** grant, not a static key. Ask the account owner to add
  you in IAM Identity Center, then:
  ```bash
  aws configure sso          # SSO start URL: https://identitycenter.amazonaws.com/ssoins-82596a7dc8914808
  aws sso login --profile Marcus
  aws sts get-caller-identity --profile Marcus   # should report account 859108043010
  ```
- The full live resource inventory is in
  [components/aws-infrastructure.md](../components/aws-infrastructure.md).

## Things to be aware of

- **The API host is a small `t3.micro` and has had memory-pressure outages.** If the site's API
  calls fail, the box may be impaired; the fix is a **reboot** (never stop/start — that changes the
  public IP `16.176.4.41` and breaks CloudFront + the frontend's hardcoded URL). See
  [reference/known-issues.md](../reference/known-issues.md) #1.
- **The API has no auth yet** and the DB is publicly reachable — fine for marking, but don't treat
  the deployment as production-secure.
- **Real interviews cost money** (OpenAI, ElevenLabs, recall.ai, Fargate). See
  [costing/COSTING.md](../costing/COSTING.md).
- **A real interview needs a Zoom join** and the third-party services (OpenAI, recall.ai,
  ElevenLabs, ngrok) to be up. A **valid student email is not required** — the bot always writes
  the join link back to the dashboard and prints it to the logs (`[trigger] Join URL: …`); the
  SMTP email is only a convenience that makes headless runs smoother. For a no-dependencies look at
  the bot's behaviour, run the offline test runner or face simulator locally
  ([build/2](2-build-run-local.md)).
