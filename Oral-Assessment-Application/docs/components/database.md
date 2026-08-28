# Database — MySQL on RDS

The shared data store for the whole system. Reached **only through the [API](backend-api.md)** —
no other component opens a MySQL connection directly.

## Current state (verified live)

- **Instance:** RDS `interviewdb`, MySQL **8.4.8**, `db.t4g.micro`, 20 GB, **publicly accessible**.
- **Endpoint:** `interviewdb.c2loht3fr432.ap-southeast-2.rds.amazonaws.com:3306`.
- **Database name:** `interviewDb`.
- **Credentials:** `admin` / `BugWriters2026`, in `backend/InterviewApi/appsettings.json`
  (`ConnectionStrings:Default`). This is the one committed secret remaining in the repo — see
  [known issues](../reference/known-issues.md) and [reference/secrets.md](../reference/secrets.md).
- **Network:** in the default VPC `vpc-03c095e1e9831c6dd`, AZ ap-southeast-2c. Security group
  `interview-app-sg` (sg-0e03f14f32f51ab2b) currently allows `3306` from `0.0.0.0/0` (plus a
  specific admin IP) — i.e. the DB is open to the internet (a hardening item).

## Schema

An entity relationship diagram of the full schema is in
[../diagrams/DATABASE_ERD.md](../diagrams/DATABASE_ERD.md).

The canonical from-scratch schema is `backend/InterviewApi/Data/sql/000_local_full_schema.sql`;
additive changes are numbered migrations in the same folder (`001_add_mode_fields.sql`,
`002_add_instructors_and_classes.sql`, `003_assignment_owns_rubric_and_result_link.sql`), applied
**by hand** — there is no migration runner. `MatchNamesWithUnderscores` maps MySQL `snake_case` to
C# `PascalCase`. **No DDL foreign keys** are defined; relationships are enforced in application code.

| Table | Key columns | Notes |
|---|---|---|
| `interview` | `id, student_id, zoom_id, transcript, start_time, status, duration, due_date, additional_info, assignment_id, student_submission, result_id` | `student_submission` (001) holds per-student work for `submission` mode; `result_id` (003) equals `interview.id` once marked. |
| `user` | `student_id (PK), username, email` | Students only; instructors are separate. |
| `rubric` | `id, rubric_contents` | `rubric_contents` is JSON `{criterion: {description, weight}}`. |
| `zoom` | `id, url, meeting_id` | `meeting_id` is INT and can't hold Zoom's 10–11 digit ID; the bot stores `0` and keeps the real ID in memory (a known bug). |
| `result` | `id, transcript, grade, feedback` | `grade` is a packed string like `Criterion: 8/10 \| … \|\| TOTAL: 42/50`. |
| `assignment` | `id, name, contents, mode, knowledge_base, questions, class_id, rubric_id` | `mode ∈ manual\|submission\|knowledge_base`; `questions` is JSON `[{text, weight}]`; `class_id` (002) links to a class; `rubric_id` (003) — the assignment owns its rubric. |
| `instructor` | `id (PK, 9-digit, not auto-increment), name` | Added in 002. |
| `class` | `id (PK auto), name, instructor_id` | One owning instructor per class. Quoted as `` `class` `` in SQL. Added in 002. |
| `class_student` | `class_id, student_id` (composite PK) | Many-to-many enrolment; `INSERT IGNORE` makes re-enrolment idempotent. Added in 002. |

## How to access

- **Best practice:** go through the API. The bot and frontend never connect directly.
- **Direct (admin/inspection):** because the instance is public you can connect with any MySQL
  client:
  ```bash
  mysql -h interviewdb.c2loht3fr432.ap-southeast-2.rds.amazonaws.com -P 3306 -u admin -p interviewDb
  ```
- **Backups:** point-in-time SQL dumps are in the repo at `backups/` (see `backups/README.md`).
  Restore with `mysql … interviewDb < dump.sql`. Treat as sensitive — they may contain student data.
