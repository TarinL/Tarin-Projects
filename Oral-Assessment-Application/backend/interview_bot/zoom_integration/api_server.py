"""
api_server.py — FastAPI trigger server for the interview bot.

Exposes a single endpoint that the student dashboard calls to kick off a
Zoom interview session on demand.

Usage:
    uvicorn api_server:app --host 0.0.0.0 --port 8080

Endpoints:
    POST /start/{interview_id}   Create meeting, launch bot, return immediately
    GET  /health                 ECS health check
"""

import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[3] / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent))   # interview_bot/
sys.path.insert(0, str(Path(__file__).parent))           # zoom_integration/

from fastapi import FastAPI, HTTPException

import db_client
from zoom_client import create_meeting, end_meeting

app = FastAPI()

# Track in-progress sessions so we reject duplicate start requests.
_active: set[int] = set()
_lock = threading.Lock()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start/{interview_id}")
def start_interview(interview_id: int):
    with _lock:
        if interview_id in _active:
            raise HTTPException(
                status_code=409,
                detail=f"Session already running for interview {interview_id}",
            )
        _active.add(interview_id)

    try:
        record = db_client.get_interview(interview_id)

        duration_secs = record.get("duration", 600)
        duration_mins = max(1, duration_secs // 60)
        start_time = record.get("startTime") or datetime.now(timezone.utc).isoformat()

        assignment_name = ((record.get("assignment") or {}).get("name") or "").strip()
        meeting_topic = f"Oral Assessment: {assignment_name}" if assignment_name else "Oral Assessment"

        print(f"[api_server] Creating Zoom meeting for interview {interview_id}…", flush=True)
        meeting = create_meeting(
            topic=meeting_topic,
            start_time_iso=start_time,
            duration_minutes=duration_mins,
        )
        join_url = meeting["join_url"]
        meeting_id_str = meeting["meeting_id"]

        # Create a new zoom record with the real URL and update the interview to reference it.
        # Store 0 for meetingId — the .NET schema uses int32 which can't hold
        # Zoom's 10-11 digit meeting IDs. The real ID is kept in meeting_id_str
        # and used directly for end_meeting().
        new_zoom_id = db_client.create_zoom(join_url, 0)
        db_client.update_interview(
            interview_id,
            db_client.interview_payload(record, status="starting", zoom_id=new_zoom_id),
        )
        print(f"[api_server] Zoom meeting created: {meeting_id_str} — launching session…", flush=True)

    except Exception:
        with _lock:
            _active.discard(interview_id)
        raise

    thread = threading.Thread(
        target=_run_session,
        args=(interview_id, join_url, meeting_id_str),
        daemon=True,
    )
    thread.start()

    return {"status": "starting", "interview_id": interview_id}


def _run_session(interview_id: int, join_url: str, meeting_id_str: str) -> None:
    try:
        # Load a fresh config from the API for this interview.
        from config import load_config_from_api
        import config as _cfg_module
        _cfg_module.cfg = load_config_from_api(interview_id)

        from session import run_zoom_interview
        run_zoom_interview(join_url, interview_id=interview_id)

    except Exception as exc:
        print(f"[api_server] Session {interview_id} failed: {exc}", flush=True)
        try:
            record = db_client.get_interview(interview_id)
            db_client.update_interview(
                interview_id,
                db_client.interview_payload(record, status="failed"),
            )
        except Exception:
            pass

    finally:
        try:
            end_meeting(meeting_id_str)
            print(f"[api_server] Zoom meeting {meeting_id_str} ended.", flush=True)
        except Exception as exc:
            print(f"[api_server] WARNING: could not end meeting {meeting_id_str}: {exc}", flush=True)

        with _lock:
            _active.discard(interview_id)
