-- 000_local_full_schema.sql
-- LOCAL DEV/TEST ONLY — never run this against RDS / production. It DROPs every table.
--
-- A from-scratch schema for the whole interview DB, reconstructed from the C#
-- models + InterviewRepository.cs SQL, with the 001 migration columns already
-- included (mode/knowledge_base/questions on assignment, student_submission on
-- interview). Use this to stand up a local MySQL the .NET API can run against so
-- you can exercise the live-stack checks (generation, seeding, config-load, edit).
--
--   docker run --rm -d --name iv-stack -e MYSQL_ROOT_PASSWORD=test \
--     -e MYSQL_DATABASE=interviewDb -p 3307:3306 \
--     -v "$PWD/backend/InterviewApi/sql:/sql:ro" mysql:8.4
--   until docker exec iv-stack mysqladmin ping -ptest --silent 2>/dev/null; do sleep 2; done
--   docker exec iv-stack sh -c "mysql -ptest interviewDb -e 'SOURCE /sql/000_local_full_schema.sql'"

DROP TABLE IF EXISTS interview;
DROP TABLE IF EXISTS class_student;
DROP TABLE IF EXISTS `class`;
DROP TABLE IF EXISTS instructor;
DROP TABLE IF EXISTS assignment;
DROP TABLE IF EXISTS rubric;
DROP TABLE IF EXISTS zoom;
DROP TABLE IF EXISTS result;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
  student_id INT PRIMARY KEY,
  username   VARCHAR(255),
  email      VARCHAR(255)
);

CREATE TABLE zoom (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  url        VARCHAR(512),
  meeting_id INT
);

CREATE TABLE rubric (
  id              INT PRIMARY KEY AUTO_INCREMENT,
  rubric_contents LONGTEXT
);

CREATE TABLE instructor (
  id   INT PRIMARY KEY,
  name VARCHAR(255)
);

CREATE TABLE `class` (
  id            INT PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(255),
  instructor_id INT
);

CREATE TABLE class_student (
  class_id   INT,
  student_id INT,
  PRIMARY KEY (class_id, student_id)
);

CREATE TABLE assignment (
  id             INT PRIMARY KEY AUTO_INCREMENT,
  name           VARCHAR(255) NULL,
  contents       TEXT,
  mode           VARCHAR(32) NOT NULL DEFAULT 'manual',
  knowledge_base LONGTEXT NULL,
  questions      LONGTEXT NULL,
  class_id       INT NULL,
  rubric_id      INT NULL          -- FK -> rubric.id; the assignment owns its rubric
);

CREATE TABLE interview (
  id                 INT PRIMARY KEY AUTO_INCREMENT,
  student_id         INT,
  zoom_id            INT,
  transcript         LONGTEXT,
  start_time         DATETIME,
  status             VARCHAR(32),
  duration           INT,
  due_date           DATETIME,
  additional_info    TEXT,
  assignment_id      INT,
  student_submission LONGTEXT NULL,
  result_id          INT NULL          -- FK -> result.id; equals interview.id once marked
);

CREATE TABLE result (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  transcript LONGTEXT,
  grade      VARCHAR(512),
  feedback   LONGTEXT
);
