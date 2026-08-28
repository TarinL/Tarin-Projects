"""
config.py — Loads interview configuration and exposes typed helpers.

Two loading modes:
  1. Local file (default / dev):  reads interview_config.json as before.
  2. API mode (ECS / production): set INTERVIEW_ID env var to fetch from the
     .NET REST API; interview_config.json is still used as a defaults template
     for fields the API doesn't yet return (LLM settings, audio settings, etc.).
"""

import json
import os
from pathlib import Path

# Mode / knowledge_base / questions live on the assignment (shared across students);
# student_submission lives on the interview (per-student).

# Resolve config path relative to this file so the project can be run
# from any working directory.
_CONFIG_PATH = Path(__file__).parent / "interview_config.json"


def load_config(path: str | Path = _CONFIG_PATH) -> dict:
    """Load and return the raw config dict from the JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config_from_api(interview_id: int) -> dict:
    """Fetch interview config from the .NET REST API and merge with local defaults.

    DB values override matching keys; all other settings (LLM, audio, interview
    timing, questions) fall through from interview_config.json until the API
    exposes them.
    """
    from db_client import get_interview  # local import avoids circular dep at module load

    data = get_interview(interview_id)

    # Start from the local defaults template so every key the bot expects exists.
    base = load_config()

    # ── Map API response fields onto the config dict ──────────────────────────
    base["student"]["id"] = data["user"]["studentId"]
    base["student"]["name"] = data["user"]["username"]

    # rubricContents is an opaque string for now; store it for prompt use.
    # TODO: parse as JSON if the backend team encodes structured rubric data here.
    # The rubric can be null (e.g. a Knowledge Base assignment has no rubric), so
    # guard against it. The API is authoritative — an absent rubric means empty, not
    # a fall-back to the local template (that would leak dev content into grading).
    rubric = data.get("rubric") or {}
    base["assignment"]["rubric"]["description"] = rubric.get("rubricContents") or ""

    # Assignment-level config drives the interview mode. Fall back to the local
    # template only when the API omits a value.
    assignment = data.get("assignment") or {}

    # The assignment name set by the instructor drives the interview "topic"
    # used in the meeting title and student email. Fall back to the local
    # template only when the API omits a name.
    assignment_name = (assignment.get("name") or "").strip()
    if assignment_name:
        base["assignment"]["topic"] = assignment_name
        # The DB has a single assignment name (no separate topic), so drive both
        # fields from it. Otherwise assignment["name"] keeps the local template
        # default and leaks dev content (e.g. "Photosynthesis Fundamentals") into
        # prompts that reference the name, such as the closing statement.
        base["assignment"]["name"] = assignment_name

    mode = (assignment.get("mode") or "").strip()
    if mode:
        base["mode"] = mode

    # Knowledge base (knowledge_base mode) lives on the assignment. The API is
    # authoritative here — an empty value means this assignment has no KB, so we
    # must NOT fall back to the local template (that would leak dev content into
    # every interview).
    base["knowledge_base"] = assignment.get("knowledgeBase") or ""

    # Questions / lines of questioning are stored as a JSON string on the
    # assignment. Parse them; keep the local defaults if absent or malformed.
    questions_raw = assignment.get("questions")
    if questions_raw:
        try:
            parsed_questions = json.loads(questions_raw)
            if isinstance(parsed_questions, list) and parsed_questions:
                base["questions"] = parsed_questions
        except (json.JSONDecodeError, TypeError):
            print(
                "[config] WARNING: assignment.questions was not valid JSON; "
                "using local default questions.",
                flush=True,
            )

    # Student submission (submission mode) is a per-interview field. API is
    # authoritative — empty means this student has no submission, so don't fall
    # back to the local template.
    base["student_submission"] = data.get("studentSubmission") or ""

    # Interview length: the DB stores `duration` in SECONDS (the trigger/api_server
    # already read it that way for the Zoom meeting window). Honour the instructor's
    # chosen duration for the interview time-limit too; the local config is the
    # fallback when the record has no duration.
    duration_secs = data.get("duration")
    if duration_secs:
        base["interview"]["duration_minutes"] = max(1, int(duration_secs) // 60)

    base["scheduling"]["scheduled_start"] = data["startTime"]
    base["scheduling"]["student_email"] = data["user"].get("email", "")

    # zoom may be null if the meeting hasn't been created yet — the bot creates
    # it when the ECS task starts.
    zoom_data = data.get("zoom") or {}
    base["scheduling"]["zoom_url"] = zoom_data.get("url") or ""
    base["scheduling"]["meeting_id"] = zoom_data.get("meetingId", 0)

    # Carry the DB record id through so downstream code can reference it.
    base["_db_interview_id"] = data["id"]

    # Preserve the full raw response so write-back code has access to all
    # foreign-key IDs (zoomId, duration, dueDate, assignmentId, resultId)
    # without re-fetching from the API.
    base["_db_raw"] = data

    return base


# ── Module-level singleton ────────────────────────────────────────────────────
# Import `cfg` anywhere in the project to access the full config dict.
# When INTERVIEW_ID is set the config is fetched from the REST API at import time.
_INTERVIEW_ID = os.environ.get("INTERVIEW_ID")
if _INTERVIEW_ID:
    print(f"[config] Loading interview {_INTERVIEW_ID} from API…", flush=True)
    cfg: dict = load_config_from_api(int(_INTERVIEW_ID))
else:
    cfg: dict = load_config()


# ── Typed convenience accessors ───────────────────────────────────────────────


def get_student(config: dict = cfg) -> dict:
    return config["student"]


def get_assignment(config: dict = cfg) -> dict:
    return config["assignment"]


def get_interview_settings(config: dict = cfg) -> dict:
    return config["interview"]


def get_questions(config: dict = cfg) -> list[tuple[str, int]]:
    """Return questions as (text, weight) tuples, matching the existing interface."""
    return [(q["text"], q["weight"]) for q in config["questions"]]


def get_student_submission(config: dict = cfg) -> str:
    """Return the student's submitted work as plain text.

    Empty string => default content-knowledge mode. A non-empty value switches
    the bot into submission-focused questioning.
    """
    return (config.get("student_submission") or "").strip()


def get_knowledge_base(config: dict = cfg) -> str:
    """Return the instructor-provided course content as plain text.

    Used in knowledge_base mode as reference context for the bot's questioning.
    """
    return (config.get("knowledge_base") or "").strip()


def get_mode(config: dict = cfg) -> str:
    """Return the interview mode: 'manual', 'submission', or 'knowledge_base'.

    When the config omits an explicit `mode`, infer it for backwards
    compatibility: 'submission' if a student submission is present, else
    'manual'.
    """
    mode = (config.get("mode") or "").strip()
    if mode:
        return mode
    return "submission" if get_student_submission(config) else "manual"


def get_llm_settings(config: dict = cfg) -> dict:
    return config["llm"]


def get_additional_instructions(config: dict = cfg) -> str:
    return config.get("system_prompt", {}).get("additional_instructions", "")


def get_audio_settings(config: dict = cfg) -> dict:
    return config.get("audio", {})
