# Frontend — InstructorDash

The web app instructors and students use. Source: `InstructorDash/`.

## Current state

- **Stack:** Create React App — React 19, react-router-dom 7, axios. Auth via AWS Cognito
  (`aws-amplify`).
- **Source layout** (`InstructorDash/src/`, after the June 2026 restructure):
  - `App.js` — top-level app, routing, and Cognito auth gating.
  - `pages/` — top-level pages (`Login.jsx`).
  - `components/instructor/` — instructor dashboard (assignments, classes, scheduling).
  - `components/student/` — student dashboard (upcoming/completed interviews, triggering).
  - `components/gradebook/` — interview review and grade display.
  - `hooks/` (`useAuth.js`), `config/` (`awsConfig.js`), `styles/`.
- **Routes** (`App.js`):
  - `/instructor/dashboard` — create assignments, schedule interviews.
  - `/instructor/interviews` — list of scheduled interviews.
  - `/report/:id` — gradebook for one interview.
  - `/student/dashboard` — student view: start an interview against an assignment.
- **Auth:** `config/awsConfig.js` configures Amplify against Cognito user pool
  `ap-southeast-2_9OMhJP0FG`, app client `2rdo1hk080nq8pdame6jv3v0jp` (`capstone-webapp`).
  Users belong to the `Teachers` or `Students` Cognito group. Note: the API does **not** yet
  validate the Cognito JWT (see [known issues](../reference/known-issues.md)).
- **API it calls:** the components currently **hardcode** `http://16.176.4.41:5000/api/...`
  (the EC2 .NET API). Endpoints used: `POST /api/assignment`, `/api/rubric`, `/api/zoom`,
  `/api/interview`, `POST /api/interview/{id}/start`, `GET /api/interview/{id}`,
  `GET /api/result/{id}`. See [backend-api.md](backend-api.md) for the full list.

## How to access

- **Deployed (best):** open `https://d7o47tp7r931l.cloudfront.net`. Served from S3 via
  CloudFront. This is the URL to give markers. See
  [build/1-access-deployed.md](../build/1-access-deployed.md).
- **Locally:** `cd InstructorDash && npm install && npm start` → `http://localhost:3000`. By
  default it still talks to the deployed EC2 API (the URL is hardcoded). See
  [build/2-build-run-local.md](../build/2-build-run-local.md).

## Hosting

Built static files live in S3 bucket `test-18-may-instructordash` (ap-southeast-2), served
through CloudFront distribution `ESSBPX2SEQR6S` at `https://d7o47tp7r931l.cloudfront.net`.
CloudFront origins/behaviors (verified live):

- default and `/static/*` → the S3 bucket (static React build).
- `/api/*` → `16.176.4.41.nip.io` (the EC2 .NET API, http-only origin).
- `/start/*` → the same EC2 API origin.

So the React app *could* call `/api/...` on its own origin and let CloudFront proxy to the
backend over https. The hardcoded `http://16.176.4.41:5000` URLs currently bypass that (a known
cleanup item — it is both mixed-content and skips the cache behaviour).

## Secrets / config

The frontend holds **no secrets** — only the public Cognito pool/client IDs in
`config/awsConfig.js`. Deploy access (AWS SSO) is covered in `InstructorDash/DEPLOY.md` and
[build/3-build-deploy-production.md](../build/3-build-deploy-production.md).
