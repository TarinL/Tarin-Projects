"""
seed_interview.py — Create a test interview in the database from interview_config.json.

Usage:
    python seed_interview.py

Reads interview_config.json and POSTs:
  1. User (student)
  2. Zoom record
  3. Rubric
  4. Assignment
  5. Interview (links all of the above)

Prints the new interview ID on success — copy it into INTERVIEW_ID in your .env.

The interview mode is whatever interview_config.json is currently set to, so this
script seeds all three modes:
  - manual:         leave student_submission and knowledge_base empty in the config.
  - submission:     python apply_to_config.py --submission <file.txt>  (then seed).
  - knowledge_base: python kb_generator.py <kb.txt> --num-questions N --out a.json
                    then python apply_to_config.py --kb-assessment a.json  (then seed).
"""

import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

BASE_URL = os.environ.get("DB_API_BASE_URL", "").rstrip("/")
if not BASE_URL or BASE_URL == "http://PLACEHOLDER":
    sys.exit("ERROR: set DB_API_BASE_URL in your .env (e.g. http://16.176.4.41:5000)")

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
TIMEOUT = 10


def get(path: str):
    url = BASE_URL + path
    r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 404:
        return None
    if not r.is_success:
        sys.exit(f"ERROR: GET {path} returned {r.status_code}: {r.text}")
    return r.json()


def post(path: str, body: dict):
    url = BASE_URL + path
    r = httpx.post(url, json=body, headers=HEADERS, timeout=TIMEOUT)
    if not r.is_success:
        sys.exit(f"ERROR: POST {path} returned {r.status_code}: {r.text}")
    return r.json()


def extract_id(result) -> int:
    """Return the numeric ID from whatever shape the API sends back."""
    if isinstance(result, int):
        return result
    if isinstance(result, dict):
        return int(result.get("id", 0))
    # plain stringified int or message like "Zoom added. Zoom Id: 2"
    try:
        return int(str(result).strip())
    except (TypeError, ValueError):
        match = re.search(r"\d+", str(result))
        if match:
            return int(match.group())
        sys.exit(f"ERROR: could not extract id from API response: {result!r}")


def main():
    config_path = Path(__file__).parent.parent / "interview_config.json"
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    student = cfg["student"]
    scheduling = cfg["scheduling"]
    assignment_cfg = cfg["assignment"]
    rubric_cfg = assignment_cfg["rubric"]
    interview_cfg = cfg["interview"]

    # 1. Ensure user exists
    student_id = int(student["id"])
    existing_user = get(f"/api/user/{student_id}")
    if existing_user:
        print(f"User {student_id} already exists, skipping creation.")
    else:
        print("Creating user…")
        user_body = {
            "studentId": student_id,
            "username": student["name"],
            "email": scheduling.get("student_email", ""),
        }
        post("/api/user", user_body)
        print(f"  studentId: {student_id}")

    # 2. Create zoom record (use placeholder URL/meetingId for test seeds)
    print("Creating zoom record…")
    zoom_body = {
        "id": 0,
        "url": scheduling.get("zoom_url", "https://zoom.us/j/00000000000"),
        "meetingId": int(scheduling.get("meeting_id", 0)),
    }
    zoom_result = post("/api/zoom", zoom_body)
    zoom_id = extract_id(zoom_result)
    print(f"  zoomId: {zoom_id}")

    # 3. Create rubric (serialize structured rubric dict to JSON string)
    print("Creating rubric…")
    rubric_body = {
        "id": 0,
        "rubricContents": json.dumps(rubric_cfg),
    }
    rubric_result = post("/api/rubric", rubric_body)
    rubric_id = extract_id(rubric_result)
    print(f"  rubricId: {rubric_id}")

    # 4. Create assignment (mode / knowledge_base / questions are assignment-level;
    #    the assignment owns the rubric via rubricId)
    print("Creating assignment…")
    assignment_body = {
        "id": 0,
        "name": assignment_cfg["name"],
        "contents": assignment_cfg.get("topic", assignment_cfg["name"]),
        "mode": cfg.get("mode", "manual"),
        "knowledgeBase": cfg.get("knowledge_base", ""),
        "questions": json.dumps(cfg.get("questions", [])),
        "rubricId": rubric_id,
    }
    print(f"  mode: {assignment_body['mode']}")
    assignment_result = post("/api/assignment", assignment_body)
    assignment_id = extract_id(assignment_result)
    print(f"  assignmentId: {assignment_id}")

    # 5. Create interview (rubric is inherited from the assignment)
    print("Creating interview…")
    interview_body = {
        "id": 0,
        "studentId": student_id,
        "zoomId": zoom_id,
        "assignmentId": assignment_id,
        "transcript": None,
        "startTime": scheduling["scheduled_start"],
        "status": "scheduled",
        "duration": interview_cfg["duration_minutes"] * 60,
        "dueDate": scheduling["scheduled_start"],
        "additionalInfo": None,
        "studentSubmission": cfg.get("student_submission", ""),
    }
    interview_result = post("/api/interview", interview_body)
    interview_id = extract_id(interview_result)

    print()
    print("=" * 50)
    print(f"  Interview created! ID = {interview_id}")
    print(f"  Add to your .env:")
    print(f"    INTERVIEW_ID={interview_id}")
    print("=" * 50)


if __name__ == "__main__":
    main()
