# VivāVoce — documentation

Everything needed to understand, run, and deploy VivāVoce (the automated AI oral-assessment
tool). Start with whichever fits your goal:

- **Just want to use the running system?** → [build/1-access-deployed.md](build/1-access-deployed.md)
- **Want to run it locally?** → [build/2-build-run-local.md](build/2-build-run-local.md)
- **Want to deploy a new version?** → [build/3-build-deploy-production.md](build/3-build-deploy-production.md)
- **Want to understand how it works?** → [ARCHITECTURE.md](ARCHITECTURE.md)

## Contents

### Overview
- [ARCHITECTURE.md](ARCHITECTURE.md) — what the system is, how a request flows, and a map to
  everything else.

### Components
- [components/frontend.md](components/frontend.md) — InstructorDash (React web app).
- [components/backend-api.md](components/backend-api.md) — InterviewApi (.NET REST API).
- [components/interview-bot.md](components/interview-bot.md) — the Python interview + marking bot.
- [components/bot-face.md](components/bot-face.md) — the live bot-face visualiser.
- [components/database.md](components/database.md) — the RDS MySQL schema.
- [components/aws-infrastructure.md](components/aws-infrastructure.md) — the live AWS resource
  inventory (verified).

### Build & deploy
- [build/1-access-deployed.md](build/1-access-deployed.md) — access the deployed build.
- [build/2-build-run-local.md](build/2-build-run-local.md) — build & run locally from a cold clone.
- [build/3-build-deploy-production.md](build/3-build-deploy-production.md) — build & deploy to AWS.

### Reference
- [reference/secrets.md](reference/secrets.md) — secret/config map (`.env` ↔ Secrets Manager ↔
  `appsettings.json`).
- [reference/known-issues.md](reference/known-issues.md) — risk register.

### Diagrams & costing
- [diagrams/SYSTEM_MAP.md](diagrams/SYSTEM_MAP.md) — service topology.
- [diagrams/INTERVIEW_BOT_FLOWCHART.md](diagrams/INTERVIEW_BOT_FLOWCHART.md) — per-phase interview
  flow.
- [diagrams/USE_CASE_DIAGRAM.md](diagrams/USE_CASE_DIAGRAM.md) — UML use case diagram.
- [diagrams/DATABASE_ERD.md](diagrams/DATABASE_ERD.md) — database entity relationship diagram.
- [diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md](diagrams/INTERVIEW_BOT_CLASS_DIAGRAM.md) — UML class
  diagram of the interview bot.
- [diagrams/LEGEND.md](diagrams/LEGEND.md) — diagram legend.
- [costing/COSTING.md](costing/COSTING.md) — per-interview cost model.

> All live AWS details in these docs were verified against account `859108043010`
> (`ap-southeast-2`) on 2026-06-12.
