"""
main.py — Entry point for the interview bot.

All configuration (student, assignment, questions, LLM settings) now comes
from interview_config.json. The CLI setup wizard has been removed — edit the
JSON file directly to change any interview parameters.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)  # must run before config imports, which read env vars at module load

import audio
import db_client
from config import (
    cfg,
    get_student,
    get_assignment,
    get_interview_settings,
    get_questions,
)
from bot import InterviewBot
from transcript_format import format_transcript


# ── CLI stubs ─────────────────────────────────────────────────────────────────
# Override audio functions so the state machine runs entirely in the terminal.
# Remove these once real TTS/STT is implemented.


def _tts_stub(text: str):
    """Print bot output to terminal instead of speaking it."""
    if text:
        print(f"\n[BOT] {text}\n")


def _stt_stub() -> str:
    """Read interviewee response from terminal instead of microphone."""
    return input("[YOU] ").strip()


"""audio.text_to_speech = _tts_stub
audio.speech_to_text = _stt_stub"""


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    student = get_student(cfg)
    assignment = get_assignment(cfg)
    interview = get_interview_settings(cfg)
    questions = get_questions(cfg)

    print("=" * 60)
    print("  Interview Bot")
    print("=" * 60)
    print(f"  Student   : {student['name']}")
    print(f"  Assignment: {assignment['name']}")
    print(f"  Topic     : {assignment['topic']}")
    print(f"  Level     : {interview['institution_level']}")
    print(f"  Duration  : {interview['duration_minutes']} min")
    print(f"  Questions : {len(questions)}")
    print(f"  Follow-ups: up to {interview['follow_up_depth']} per question")
    print("=" * 60)

    bot = InterviewBot(config=cfg)

    audio._get_tts()
    audio._get_stt()

    bot.prefetch_all()
    for text in bot._question_text_cache.values():
        audio.prefetch_tts(text)
    for text in bot._phrase_cache.values():
        audio.prefetch_tts(text)

    input("\nReady. Press Enter to begin the interview…")

    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n\n[Interview interrupted]")
        sys.exit(0)

    print("\n" + "=" * 60)
    print("  Interview complete")
    print(f"  Transcript entries: {len(bot.ctx.transcript)}")
    print("=" * 60)
    print()
    print(format_transcript(bot.ctx.transcript))

    interview_id = cfg.get("_db_interview_id")
    if interview_id:
        _write_back(bot, interview_id)


def _write_back(bot: InterviewBot, interview_id: int) -> None:
    """Push transcript to the API then trigger the marking bot."""
    raw = cfg.get("_db_raw", {})

    transcript_text = format_transcript(bot.ctx.transcript)

    payload = {
        "id": interview_id,
        "studentId": raw.get("user", {}).get("studentId"),
        "zoomId": raw.get("zoom", {}).get("id"),
        "transcript": transcript_text,
        "startTime": raw.get("startTime"),
        "status": "COMPLETED",
        "duration": raw.get("duration"),
        "dueDate": raw.get("dueDate"),
        "additionalInfo": raw.get("additionalInfo"),
        "assignmentId": raw.get("assignmentId"),
        "studentSubmission": raw.get("studentSubmission"),
    }

    print(f"\n[main] Writing transcript back to interview {interview_id}…", flush=True)
    try:
        db_client.update_interview(interview_id, payload)
        print("[main] Transcript saved.", flush=True)
    except RuntimeError as exc:
        print(f"[main] WARNING: could not save transcript — {exc}", file=sys.stderr)

    print("[main] Triggering marking bot…", flush=True)
    try:
        from marker import mark_interview
        mark_interview(interview_id)
        print("[main] Marking complete.", flush=True)
    except Exception as exc:
        print(f"[main] WARNING: marking bot failed — {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
