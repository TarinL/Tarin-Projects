-- 999_local_verify.sql
-- LOCAL VERIFICATION ONLY — never run this against RDS / production.
--
-- One-shot check that 001_add_mode_fields.sql is valid DDL and produces the
-- columns the C#/Python code expects. It:
--   1. creates minimal stubs of the two tables 001 alters (the schema as it
--      exists BEFORE the migration — reconstructed from the C# models + repo SQL),
--   2. SOURCEs the REAL 001_add_mode_fields.sql (so you test the actual script,
--      not a copy),
--   3. verifies the 4 new columns exist with the right shape + defaults.
--
-- It DROPs the assignment/interview tables first, so only ever point it at a
-- scratch database.
--
-- ── Recommended run (Docker, with the sql/ dir mounted at /sql) ─────────────
--   docker run --rm -d --name iv-verify -e MYSQL_ROOT_PASSWORD=test \
--     -e MYSQL_DATABASE=interviewDb -p 3307:3306 \
--     -v "$PWD/backend/InterviewApi/sql:/sql:ro" mysql:8.4
--   until docker exec iv-verify mysqladmin ping -ptest --silent 2>/dev/null; do sleep 2; done
--   docker exec iv-verify sh -c "mysql -ptest interviewDb -e 'SOURCE /sql/999_local_verify.sql'"
--   docker stop iv-verify
--
-- ── Host mysql client instead of Docker ─────────────────────────────────────
--   Run from the sql/ directory so the SOURCE path below resolves, e.g.:
--     cd backend/InterviewApi/sql
--     mysql -h 127.0.0.1 -P 3306 -u root -p yourscratchdb -e "SOURCE 999_local_verify.sql"
--   (and change the SOURCE line below from /sql/... to just the filename).

-- ── 1. Pre-migration stubs (schema BEFORE 001) ──────────────────────────────
DROP TABLE IF EXISTS interview;
DROP TABLE IF EXISTS assignment;

CREATE TABLE assignment (
  id       INT PRIMARY KEY AUTO_INCREMENT,
  name     VARCHAR(255) NULL,
  contents TEXT
);

CREATE TABLE interview (
  id              INT PRIMARY KEY AUTO_INCREMENT,
  student_id      INT,
  rubric_id       INT,
  zoom_id         INT,
  transcript      TEXT,
  start_time      DATETIME,
  status          VARCHAR(32),
  duration        INT,
  due_date        DATETIME,
  additional_info TEXT,
  assignment_id   INT
);

-- ── 2. Apply the REAL migration under test ───────────────────────────────────
-- Path matches the Docker recipe above (sql/ mounted at /sql). For a host
-- client run from the sql/ dir, change this to: SOURCE 001_add_mode_fields.sql
SOURCE /sql/001_add_mode_fields.sql

-- ── 3. Verify the 4 new columns exist with the right shape ───────────────────
SELECT table_name, column_name, column_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND ( (table_name = 'assignment' AND column_name IN ('mode','knowledge_base','questions'))
     OR (table_name = 'interview'  AND column_name = 'student_submission') )
ORDER BY table_name, column_name;
-- Expect 4 rows:
--   assignment.knowledge_base    longtext      YES   NULL
--   assignment.mode              varchar(32)   NO    manual
--   assignment.questions         longtext      YES   NULL
--   interview.student_submission longtext      YES   NULL

-- ── 4. Functional check: the default protects the existing create flow ──────
-- The current frontend POSTs an assignment with only {name, contents} and an
-- interview without studentSubmission. Confirm those still work post-migration.
INSERT INTO assignment (name, contents) VALUES ('legacy assignment', 'some topic');
INSERT INTO interview (student_id, rubric_id, zoom_id, status, assignment_id)
VALUES (1, 1, 1, 'SCHEDULED', LAST_INSERT_ID());

SELECT id, mode, knowledge_base, questions FROM assignment;   -- mode => 'manual', others NULL
SELECT id, status, student_submission FROM interview;         -- student_submission => NULL
