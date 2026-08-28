-- 001_add_mode_fields.sql
-- Adds the columns needed to drive the three interview modes (manual / submission /
-- knowledge_base) from the database instead of the bot's local interview_config.json.
--
-- There is no migration runner in this project; run this script once against the
-- target MySQL instance. All changes are additive — no existing column is altered
-- or dropped, so existing rows and create flows keep working.

ALTER TABLE assignment
  ADD COLUMN mode VARCHAR(32) NOT NULL DEFAULT 'manual',
  ADD COLUMN knowledge_base LONGTEXT NULL,
  ADD COLUMN questions LONGTEXT NULL;          -- JSON array of {text, weight}

ALTER TABLE interview
  ADD COLUMN student_submission LONGTEXT NULL;
