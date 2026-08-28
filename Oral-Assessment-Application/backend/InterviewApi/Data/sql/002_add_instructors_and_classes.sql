-- 002_add_instructors_and_classes.sql
-- Adds instructor records to the database (previously instructors lived only in
-- Cognito) plus classes, class enrolment, and a class link on assignments.
--
-- There is no migration runner in this project; run this script once against the
-- target MySQL instance. All changes are additive — no existing column is altered
-- or dropped, so existing rows and create flows keep working.

CREATE TABLE instructor (
  id   INT PRIMARY KEY,           -- 9-digit ID entered at account creation (not auto-increment)
  name VARCHAR(255)
);

CREATE TABLE `class` (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(255),
  instructor_id INT                -- FK -> instructor.id (app-enforced, matching project convention)
);

CREATE TABLE class_student (
  class_id   INT,
  student_id INT,
  PRIMARY KEY (class_id, student_id)
);

ALTER TABLE assignment
  ADD COLUMN class_id INT NULL;    -- FK -> class.id; nullable so existing assignments keep working
