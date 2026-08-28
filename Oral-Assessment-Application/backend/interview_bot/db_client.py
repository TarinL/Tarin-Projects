"""
db_client.py — HTTP client for the .NET interview REST API.

Configuration via environment variables:
    DB_API_BASE_URL   Base URL of the .NET API (e.g. http://16.176.4.41:5000)

The API has no authentication scheme — no token required.
"""

import os
import re
from datetime import datetime, timezone

import httpx

_TIMEOUT_SECONDS = 10

_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def _url(path: str) -> str:
    base = os.environ.get("DB_API_BASE_URL", "http://PLACEHOLDER").rstrip("/")
    return base + path


def get_interview(interview_id: int) -> dict:
    """Fetch an InterviewDetail record from the REST API.

    Returns a dict with shape:
        {
            "id": int,
            "startTime": str,          # ISO 8601
            "status": str,
            "transcript": str | None,
            "duration": int,
            "dueDate": str,
            "additionalInfo": str | None,
            "assignmentId": int,
            "resultId": int | None,            # FK to result.id; equals interview id once marked
            "studentSubmission": str | None,   # per-student work (submission mode)
            "user": {"studentId": int, "username": str, "email": str},
            "rubric": {"id": int, "rubricContents": str},   # sourced from the assignment's rubric
            "zoom": {"id": int, "url": str, "meetingId": int},
            "assignment": {
                "id": int,
                "name": str | None,
                "contents": str,
                "mode": str,               # manual | submission | knowledge_base
                "knowledgeBase": str | None,
                "questions": str | None,   # JSON array of {text, weight}
                "rubricId": int | None     # the assignment owns its rubric
            }
        }
    """
    try:
        response = httpx.get(
            _url(f"/api/interview/{interview_id}"),
            headers=_HEADERS,
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"[db_client] API returned {exc.response.status_code} for interview {interview_id}: "
            f"{exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"[db_client] Could not reach API at {exc.request.url}: {exc}") from exc
    return response.json()


def update_interview(interview_id: int, data: dict) -> str:
    """Update an interview record via PUT /api/interview/{id}.

    data must match the Interview schema:
        {
            "id": int,
            "studentId": int,
            "zoomId": int,
            "transcript": str | None,
            "startTime": str,          # ISO 8601
            "status": str,
            "duration": int,
            "dueDate": str,
            "additionalInfo": str | None,
            "assignmentId": int,
            "resultId": int | None
        }
    """
    try:
        response = httpx.put(
            _url(f"/api/interview/{interview_id}"),
            headers=_HEADERS,
            json=data,
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"[db_client] PUT interview {interview_id} failed ({exc.response.status_code}): "
            f"{exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"[db_client] Could not reach API at {exc.request.url}: {exc}") from exc
    return response.text


def finish_interview(interview_id: int, status: str, transcript: str | None) -> None:
    """PATCH /api/interview/{id}/finish — write terminal status + transcript.

    status must be "COMPLETED" or "FAILED". transcript overwrites any existing value.
    """
    try:
        response = httpx.patch(
            _url(f"/api/interview/{interview_id}/finish"),
            headers=_HEADERS,
            json={"status": status, "transcript": transcript},
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"[db_client] PATCH finish interview {interview_id} failed ({exc.response.status_code}): "
            f"{exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"[db_client] Could not reach API at {exc.request.url}: {exc}") from exc


def create_zoom(url: str, meeting_id: int) -> int:
    """Create a zoom record and return the new zoom id."""
    try:
        response = httpx.post(
            _url("/api/zoom"),
            headers=_HEADERS,
            json={"id": 0, "url": url, "meetingId": meeting_id},
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"[db_client] POST /api/zoom failed ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"[db_client] Could not reach API at {exc.request.url}: {exc}") from exc
    raw = response.text.strip().strip('"')
    match = re.search(r"\d+", raw)
    if not match:
        raise RuntimeError(f"[db_client] Could not extract zoom id from response: {raw!r}")
    return int(match.group())


def mark_ready(interview_id: int) -> None:
    """Signal that the bot is in the call and the interview is about to begin.

    Sets status to "READY" (the loading screen polls for this to reveal the join
    button without guessing a fixed wait) and stamps startTime to the actual start
    moment so the gradebook shows when the interview really ran (the scheduled slot
    was stored at creation time). Best-effort — never re-raise.
    """
    try:
        record = get_interview(interview_id)
        payload = interview_payload(record, status="READY")
        payload["startTime"] = datetime.now(timezone.utc).isoformat()
        update_interview(interview_id, payload)
    except Exception as exc:
        print(f"[db_client] WARNING: could not mark interview {interview_id} ready: {exc}", flush=True)


def interview_payload(record: dict, *, status: str | None = None, transcript: str | None = None, zoom_id: int | None = None) -> dict:
    """Build a PUT /api/interview payload from a GET response, optionally overriding fields."""
    return {
        "id": record["id"],
        "studentId": record["user"]["studentId"],
        "zoomId": zoom_id if zoom_id is not None else record["zoom"]["id"],
        "transcript": transcript if transcript is not None else record.get("transcript"),
        "startTime": record["startTime"],
        "status": status if status is not None else record["status"],
        "duration": record["duration"],
        "dueDate": record["dueDate"],
        "additionalInfo": record.get("additionalInfo"),
        "assignmentId": record["assignmentId"],
        "studentSubmission": record.get("studentSubmission"),
        "resultId": record.get("resultId"),
    }
