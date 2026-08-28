-- 003_assignment_owns_rubric_and_result_link.sql
-- Moves rubric ownership from the interview onto the assignment, and makes the
-- interview <-> result relationship 1:1 with a shared id.
--
-- Rationale:
--   * Previously each interview created its own rubric (a copy of
--     assignment.contents), so rubrics were duplicated and could drift from the
--     assignment that generated the questions. The rubric belongs on the
--     assignment (which already owns `questions`).
--   * Results were inserted with an auto-increment id unrelated to the
--     interview, but the dashboard already fetches grades via
--     GET /api/result/{interviewId}. Making result.id == interview.id (and
--     recording it on interview.result_id) fixes that lookup.
--
-- There is no migration runner in this project; run this script once against the
-- target MySQL instance. All steps are additive EXCEPT the final DROP of
-- interview.rubric_id, which is performed only after the backfill below.

-- 1. assignment owns the rubric
ALTER TABLE assignment
  ADD COLUMN rubric_id INT NULL;          -- FK -> rubric.id (app-enforced, matching project convention)

-- 2. backfill: each assignment inherits a rubric from one of its existing
--    interviews (the most recent rubric_id wins; all per-interview rubrics were
--    copies of the same assignment.contents, so any is equivalent).
UPDATE assignment a
JOIN (
  SELECT assignment_id, MAX(rubric_id) AS rubric_id
  FROM interview
  WHERE assignment_id IS NOT NULL AND rubric_id IS NOT NULL
  GROUP BY assignment_id
) m ON m.assignment_id = a.id
SET a.rubric_id = m.rubric_id
WHERE a.rubric_id IS NULL;

-- 3. interview <-> result is 1:1; result.id == interview.id
ALTER TABLE interview
  ADD COLUMN result_id INT NULL;          -- FK -> result.id; equals interview.id once marked

-- 4. drop the now-unused per-interview rubric link (after the backfill in step 2).
--    On environments with a real FK on interview.rubric_id (e.g. production, where
--    it is named interview_ibfk_2 -> rubric.id) the constraint must be dropped
--    first. The constraint name may differ between environments; look it up with:
--      SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
--      WHERE TABLE_NAME='interview' AND COLUMN_NAME='rubric_id'
--        AND REFERENCED_TABLE_NAME='rubric';
ALTER TABLE interview
  DROP FOREIGN KEY interview_ibfk_2;

ALTER TABLE interview
  DROP COLUMN rubric_id;
