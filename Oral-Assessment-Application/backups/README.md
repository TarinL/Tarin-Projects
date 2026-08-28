# Database backups

Point-in-time SQL dumps of the production `interviewDb` (MySQL 8.4 on AWS RDS),
kept for disaster recovery and reference.

- `interviewDb-prod-20260608-155400.sql`
- `interviewDb-prod-20260608-155440.sql`

(Taken 2026-06-08.)

Restore example:

```bash
mysql -h <host> -u <user> -p interviewDb < interviewDb-prod-20260608-155440.sql
```

Note: these dumps may contain student/instructor personal data — treat as
sensitive and do not redistribute.
