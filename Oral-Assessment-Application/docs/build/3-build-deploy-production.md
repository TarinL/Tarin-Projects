# 3. Build & deploy to AWS

How to push a new version of each component to the live deployment. All commands assume the
`Marcus` SSO profile in account `859108043010`, region `ap-southeast-2`:

```bash
aws sso login --profile Marcus
aws sts get-caller-identity --profile Marcus     # must report account 859108043010
```

Deploy each component independently — they don't have to go together.

## Frontend → S3 + CloudFront

The "live site" is **not** a git push — it's a static build uploaded to S3 and a CloudFront cache
invalidation. There's a script for it:

```bash
cd InstructorDash
AWS_PROFILE=Marcus npm run deploy
```

`deploy.sh` runs `npm run build`, `aws s3 sync ./build s3://test-18-may-instructordash/ --delete`,
and `aws cloudfront create-invalidation --distribution-id ESSBPX2SEQR6S --paths "/*"`. Changes go
live in under a minute. Access (S3 write + CloudFront invalidation) is an IAM Identity Center grant
— details in `InstructorDash/DEPLOY.md`.

## Interview bot → ECR (+ ECS)

The task definition pulls `interview-bot:latest`, so pushing a new image is usually all you need —
the next interview's `RunTask` picks it up automatically.

```bash
aws ecr get-login-password --region ap-southeast-2 --profile Marcus \
  | docker login --username AWS --password-stdin \
    859108043010.dkr.ecr.ap-southeast-2.amazonaws.com

cd backend/interview_bot
docker buildx build --platform linux/amd64 \
  -t 859108043010.dkr.ecr.ap-southeast-2.amazonaws.com/interview-bot:latest \
  --push .
```

> Build for **linux/amd64** — the task runs on `X86_64` Fargate.

Only register a new task-definition revision if you change CPU/memory/env/secrets. The repo's
`task_definition.json` matches the live revision (:7, 8 vCPU / 16 GB):

```bash
aws ecs register-task-definition --cli-input-json file://task_definition.json --profile Marcus
```

Trigger one end-to-end and watch it:

```bash
curl -X POST http://16.176.4.41:5000/api/interview/123/start
aws logs tail /ecs/interview-bot --since 1m --follow --profile Marcus
```

## Backend API → EC2

The EC2 box runs the binary via the `interviewapi.service` systemd unit
(`User=ec2-user`, `WorkingDirectory=/home/ec2-user/interviewapi`). It serves
**framework-dependent** publish output — the .NET 9 *runtime* is installed but **no SDK and no
source checkout**, so you build locally and copy the artefacts up.

```bash
# on a dev machine with the .NET 9 SDK:
dotnet publish backend/InterviewApi -c Release -o ./publish
tar -czf api.tar.gz -C ./publish --exclude=appsettings.json .   # keep the box's appsettings.json
```

Get `api.tar.gz` onto the box (via SSM or S3 — there's no SSH key in the repo), then on the box:

```bash
TS=$(date +%Y%m%d-%H%M%S); APP=/home/ec2-user/interviewapi
sudo cp -a "$APP" "${APP}.bak-$TS"          # backup for rollback
sudo systemctl stop interviewapi.service
sudo tar -xzf /tmp/api.tar.gz -C "$APP"     # overlay (keeps appsettings.json + the unit's env)
sudo chown -R ec2-user:ec2-user "$APP"
sudo systemctl restart interviewapi.service
```

Connect to the box with **SSM Session Manager** (the instance role grants SSM access):

```bash
aws ssm start-session --target i-023e5be729892fe32 --profile Marcus
```

> **Never stop/start the instance** — the public IP `16.176.4.41` is not an Elastic IP, and
> changing it breaks the CloudFront `/api/*` origin and the frontend's hardcoded URL. If the box is
> impaired, **reboot** it. See [reference/known-issues.md](../reference/known-issues.md) #1.

## Database changes → RDS

There is no migration runner. Apply schema changes by hand: add a numbered script under
`backend/InterviewApi/Data/sql/` and run it against RDS:

```bash
mysql -h interviewdb.c2loht3fr432.ap-southeast-2.rds.amazonaws.com -u admin -p interviewDb \
  < backend/InterviewApi/Data/sql/00X_your_change.sql
```

Take a backup first (see `backups/`).

## Secrets

Bot secrets live in AWS Secrets Manager and are wired into `task_definition.json`. To change one,
update the secret value (the task reads it fresh on the next launch):

```bash
aws secretsmanager put-secret-value --secret-id OPENAI_API_KEY --secret-string '<new-value>' --profile Marcus
```

To add a new secret, create it and add a `{name, valueFrom}` entry to the task definition's
`secrets`, then register a new revision. Full map: [reference/secrets.md](../reference/secrets.md).
