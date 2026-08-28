# Known issues / risk register

Real items worth addressing, in roughly decreasing severity. Status reflects the live state
verified on 2026-06-12.

1. **EC2 API box runs out of memory and can hang.** The API host is a 1 GB `t3.micro`
   (`i-023e5be729892fe32`) that has also run Microsoft Defender for Endpoint and the Azure Monitor
   agent; together these exhaust RAM and the OOM-killer fires until the instance status check goes
   `impaired`, taking down both the API (`:5000`) and the SSM agent. On 2026-06-04 the box sat
   impaired for ~9 hours until a reboot. **Mitigation applied:** a 2 GB swapfile
   (`/swapfile`, in `/etc/fstab`, `vm.swappiness=10`). **Real fix:** a larger instance, drop the
   monitoring agents, or move the API to ECS Fargate behind an ALB. **Recovery note:** the public
   IP `16.176.4.41` is **not** an Elastic IP — recover with a **reboot** (preserves the IP). A
   stop/start would change the IP and break the CloudFront `/api/*` origin and the frontend's
   hardcoded URL.

2. **Committed RDS password.** `backend/InterviewApi/appsettings.json` ships the RDS connection
   string with `admin` / `BugWriters2026`. (The OpenAI key was removed from this file — it's now
   empty and read from the environment — but the DB password remains.) The connection string is
   also baked into the `interviewapi.service` systemd unit's `Environment=` on the box. **Fix:**
   move it to env/Secrets Manager, rotate the password, and scrub it from git history. Deferred for
   submission.

3. **DB and API open to the internet.** `api-server-gp` opens 5000 (and 80) to `0.0.0.0/0`, and
   `interview-app-sg` opens 3306 to `0.0.0.0/0`. The DB is reachable from anywhere. **Fix:**
   restrict 3306 to the ECS task SG + admin IPs, and front the API with https only.

4. **No auth on the .NET API.** Cognito is configured and the frontend signs in, but the controller
   does not validate the JWT — it trusts `instructor_id` / `student_id` from the body or route.
   Anyone with the public IP can read transcripts or trigger interviews. **Fix:** validate the
   Cognito token and derive the acting user from it.

5. **Marker isn't auto-invoked in the ECS path.** `session.run_zoom_interview()` writes the
   transcript and exits; the local CLI's `main._write_back()` → `mark_interview` doesn't fire in
   the container. **Fix:** invoke marking from `session.py` after the transcript is written, or add
   a `/api/interview/{id}/mark` endpoint the frontend calls.

6. **Frontend bypasses CloudFront for API calls.** Components hardcode `http://16.176.4.41:5000`,
   which is mixed-content (CloudFront is https, backend is http) and skips the `/api/*` cache
   behaviour. **Fix:** call same-origin relative `/api/...` paths and let CloudFront proxy.

7. **`zoom.meeting_id` column is INT** and can't hold a real Zoom meeting ID. The bot writes `0`
   and keeps the string ID only in memory; a crash between `create_meeting` and `end_meeting`
   orphans the meeting. **Fix:** migrate the column to `VARCHAR(32)` / `BIGINT UNSIGNED`.

8. **String-encoded grade/feedback** in `result.grade` / `result.feedback`. Parsing is fragile.
   **Fix:** a structured/JSON schema would make analytics and re-grading trivial.

9. **No ECS service / no scaling.** Tasks are launched one-by-one by `RunTask`; a stuck task isn't
   restarted and there's no desired-count control. Fine for low volume. **Fix:** a queue-driven
   model (SQS → ECS service) if concurrency rises.

10. **ngrok inside Fargate is fragile.** Free-tier ngrok rotates URLs and limits simultaneous
    tunnels. **Fix:** an AWS-native stable endpoint (e.g. tasks behind an NLB) so recall.ai can
    connect without the bounce.

## Resolved since earlier drafts

- **EC2 → AWS credentials.** The instance role `interview-api-ec2-role` now grants `ecs:RunTask`,
  `ecs:DescribeTasks/ListTasks`, and `iam:PassRole` for both task roles, plus OpenAI-secret read
  (verified live). The API host no longer needs static AWS keys in `.env` to trigger the bot.
- **Bot under-resourced for live STT.** The task definition was bumped to 8 vCPU / 16 GB
  (revision :7), and `LIVE_TRANSCRIBE=1` is now set, enabling live student captions on ECS.
