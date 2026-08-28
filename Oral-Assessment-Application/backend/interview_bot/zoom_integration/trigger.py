"""
trigger.py — Programmatic interview trigger for local / pre-AWS testing and ECS.

Two usage modes:

  Local (reads interview_config.json):
      python trigger.py [--now]

  API / ECS (fetches config from .NET REST API):
      INTERVIEW_ID=<id> python trigger.py --interview-id <id> [--now]
      -- or set INTERVIEW_ID in the environment before running.

  When --interview-id is supplied (or INTERVIEW_ID env var is set) the bot
  skips Zoom meeting creation — the DB record already contains the join URL.

Flags:
    --now           Skip the wait and launch immediately (useful for tests).
    --interview-id  Interview ID to fetch from the REST API.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Load .env before any other imports touch API clients
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parents[3] / ".env")
except (ImportError, IndexError):
    pass

sys.path.insert(0, str(Path(__file__).parents[1]))  # interview_bot/

import db_client
from config import cfg, get_student, get_assignment, get_interview_settings


def _parse_scheduled_start(raw: str) -> datetime:
    """Parse ISO 8601 string (with or without offset) into an aware datetime."""
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        print(f"[trigger] Could not parse scheduled_start: {raw!r}")
        print("          Expected ISO 8601, e.g. 2026-05-07T10:00:00+10:00")
        sys.exit(1)
    if dt.tzinfo is None:
        # Assume local time if no offset given
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt


def _wait_until(start: datetime) -> None:
    now = datetime.now(timezone.utc)
    delta = (start - now).total_seconds()
    if delta <= 0:
        print("[trigger] Scheduled time is in the past — starting immediately.")
        return
    print(f"[trigger] Waiting {delta:.0f}s until {start.isoformat()} …")
    while True:
        remaining = (start - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            break
        if remaining > 60:
            print(f"[trigger]   {remaining/60:.1f} min remaining…", flush=True)
            time.sleep(30)
        else:
            print(f"[trigger]   {remaining:.0f}s remaining…", flush=True)
            time.sleep(5)
    print("[trigger] Starting now.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger a scheduled Zoom interview")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Skip the wait and launch the bot immediately",
    )
    parser.add_argument(
        "--interview-id",
        type=int,
        default=None,
        help=(
            "Interview ID to load from the REST API. "
            "When set, Zoom meeting creation is skipped — the join URL comes from the DB record. "
            "Alternatively set the INTERVIEW_ID environment variable."
        ),
    )
    args = parser.parse_args()

    # If --interview-id was passed on the CLI but INTERVIEW_ID env var wasn't set yet,
    # we need to reload cfg from the API now (it was already loaded at import time from env).
    # The cleanest path: set the env var and reimport — but that's messy.
    # Instead, reload directly here when the CLI arg is the source of truth.
    interview_id = args.interview_id or (
        int(os.environ["INTERVIEW_ID"]) if os.environ.get("INTERVIEW_ID") else None
    )
    if interview_id is not None and not os.environ.get("INTERVIEW_ID"):
        # CLI arg supplied but env var wasn't set at import time — reload config now.
        from config import load_config_from_api
        import config as _config_module
        _config_module.cfg = load_config_from_api(interview_id)
        # Rebind the local reference so the rest of this function sees the new values.
        from config import cfg as _cfg
    else:
        _cfg = cfg

    db_mode = interview_id is not None

    # ── Read config ──────────────────────────────────────────────────────────────
    scheduling = _cfg.get("scheduling", {})
    student = get_student(_cfg)
    assignment = get_assignment(_cfg)
    interview = get_interview_settings(_cfg)

    student_name  = student["name"]
    student_email = scheduling.get("student_email")
    scheduled_raw = scheduling.get("scheduled_start")
    duration      = scheduling.get("duration_minutes", interview["duration_minutes"] + 5)
    topic         = assignment["topic"]

    if not student_email and not db_mode:
        print("[trigger] ERROR: scheduling.student_email is not set in interview_config.json")
        sys.exit(1)
    if not scheduled_raw:
        print("[trigger] ERROR: scheduled_start is missing from config / DB record")
        sys.exit(1)

    scheduled_start = _parse_scheduled_start(scheduled_raw)

    print("=" * 60)
    print("  Interview Trigger")
    print("=" * 60)
    print(f"  Student  : {student_name}" + (f" <{student_email}>" if student_email else ""))
    print(f"  Topic    : {topic}")
    print(f"  Start    : {scheduled_start.isoformat()}")
    print(f"  Duration : {duration} min")
    if db_mode:
        print(f"  Source   : REST API (interview_id={interview_id})")
    print("=" * 60)

    from zoom_client import create_meeting, end_meeting

    if db_mode:
        # ── ECS/DB mode: create Zoom meeting and write it back to the DB ──────
        # The .NET API just launched this task — no meeting exists yet.
        record = _cfg.get("_db_raw", {})
        duration_secs = record.get("duration", 600)
        duration_mins = max(1, duration_secs // 60)

        print("\n[trigger] Creating Zoom meeting…", flush=True)
        meeting = create_meeting(
            topic=f"Oral Assessment: {topic}",
            start_time_iso=scheduled_start.isoformat(),
            duration_minutes=duration_mins,
        )
        join_url   = meeting["join_url"]
        meeting_id = meeting["meeting_id"]

        # Store 0 for meetingId — the .NET schema uses int32 which can't hold
        # Zoom's 10-11 digit meeting IDs; we keep the real string for end_meeting().
        new_zoom_id = db_client.create_zoom(join_url, 0)
        db_client.update_interview(
            interview_id,
            db_client.interview_payload(record, status="STARTING", zoom_id=new_zoom_id),
        )
        print(f"[trigger] Meeting created: {meeting_id}", flush=True)
        print(f"[trigger] Join URL: {join_url}", flush=True)
    else:
        # ── Local mode: create a new Zoom meeting from local config ───────────
        print("\n[trigger] Creating Zoom meeting…", flush=True)
        meeting = create_meeting(
            topic=f"Oral Assessment: {topic}",
            start_time_iso=scheduled_start.isoformat(),
            duration_minutes=duration,
        )
        join_url   = meeting["join_url"]
        meeting_id = meeting["meeting_id"]
        print(f"[trigger] Meeting created: {meeting_id}")
        print(f"[trigger] Join URL: {join_url}")

    # ── Send email (off the critical path) ─────────────────────────────────────────
    # The SMTP round-trip takes several seconds; running it inline delays launching
    # the bot (and therefore the bot joining the call). Fire it in a background
    # thread so the student isn't waiting on an email they already expect.
    if student_email:
        print(f"\n[trigger] Sending meeting link to {student_email} (in background)…", flush=True)

        def _send_meeting_email():
            try:
                from notify import send_meeting_email
                send_meeting_email(
                    to=student_email,
                    join_url=join_url,
                    topic=topic,
                    scheduled_start=scheduled_start.strftime("%A, %d %B %Y at %I:%M %p %Z"),
                    student_name=student_name,
                )
            except Exception as exc:
                print(f"[trigger] WARNING: email failed ({exc}) — continuing anyway.")

        import threading
        threading.Thread(target=_send_meeting_email, daemon=True).start()
    else:
        print("[trigger] No student_email in config — skipping email notification.")

    # ── Wait until start time ─────────────────────────────────────────────────────
    if not args.now:
        _wait_until(scheduled_start)
    else:
        print("[trigger] --now flag set, skipping wait.")

    # ── Launch bot ────────────────────────────────────────────────────────────────
    print(f"\n[trigger] Launching interview bot for meeting {meeting_id}…", flush=True)
    if db_mode:
        record = db_client.get_interview(interview_id)
        db_client.update_interview(
            interview_id,
            db_client.interview_payload(record, status="RUNNING"),
        )
    try:
        from session import run_zoom_interview
        run_zoom_interview(join_url, interview_id=interview_id if db_mode else None)
    except Exception as exc:
        print(f"[trigger] ERROR: session failed — {exc}", flush=True)
        if db_mode:
            try:
                db_client.finish_interview(interview_id, "FAILED", None)
            except Exception:
                pass
        raise
    finally:
        if meeting_id:
            print(f"\n[trigger] Ending Zoom meeting {meeting_id}…", flush=True)
            try:
                end_meeting(meeting_id)
                print("[trigger] Meeting ended.")
            except Exception as exc:
                print(f"[trigger] WARNING: could not end meeting ({exc})")

    print(f"\n[trigger] Interview complete.")
    print(f"[trigger] Student : {student_name}" + (f" <{student_email}>" if student_email else ""))


if __name__ == "__main__":
    main()
