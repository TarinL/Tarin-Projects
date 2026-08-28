"""
test_runner.py — Run main.py headlessly with a simulated student.

Stubs audio I/O so no microphone or speakers are needed, generates student
responses via LLM, and saves a transcript file. Everything else — the state
machine, LLM question generation, timing — runs exactly as in production.

Usage:
    python test_runner.py [--profile strong|average|weak] [--out <path>]
"""

import argparse
import builtins
import sys
import time
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# Load .env from project root before any other imports that touch the OpenAI client
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parents[3] / ".env")
except ImportError:
    pass

# Allow running directly from tests/: put the bot root (the parent dir) on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Patch audio BEFORE importing main (which imports bot, which imports audio) ─
import audio
from context import InterviewState
from config import cfg, get_student, get_assignment, get_llm_settings

_log: list[tuple[str, str]] = []  # ("BOT"|"STUDENT"|"SESSION", text)
_stt_fn = None  # set after args are parsed

# ── Audio stubs ────────────────────────────────────────────────────────────────


def _tts_stub(text: str) -> None:
    if text:
        _log.append(("BOT", text))
        print(f"\n[BOT] {text}\n", flush=True)


def _stt_stub(timeout: float | None = None) -> str:
    last_q = next((t for r, t in reversed(_log) if r == "BOT"), "")
    # Auto-confirm the ready prompt so the test run doesn't stall.
    if "ready to begin" in last_q.lower():
        response = "Ready to begin"
    else:
        response = _stt_fn(last_q)
    _log.append(("STUDENT", response))
    print(f"[STU] {response}\n", flush=True)
    return response


audio.text_to_speech = _tts_stub
audio.speech_to_text = _stt_stub
audio.set_interview_start = lambda: None
audio.prefetch_tts = lambda text: None
audio._get_tts = lambda: None
audio._get_stt = lambda: None

# Auto-skip the "Press Enter to begin" prompt
builtins.input = lambda prompt="": print(f"{prompt}[auto]\n", flush=True) or ""

# ── Session-boundary hook (non-invasive — wraps InterviewBot._step) ────────────
# Injects a SESSION marker into _log each time a required question is about to
# be asked, so the transcript file shows where the context window resets.

from bot import InterviewBot

_orig_step = InterviewBot._step


def _patched_step(self, state: InterviewState) -> InterviewState:
    if state == InterviewState.ASK_QUESTION and not self._time_is_up():
        q_text = self.ctx.questions[self.ctx.question_index][0]
        _log.append(
            ("SESSION", f"Section {self.ctx.question_index + 1}: {q_text}")
        )
    elif state == InterviewState.OPEN_FLOOR:
        _log.append(("SESSION", "Open floor"))
    return _orig_step(self, state)


InterviewBot._step = _patched_step

# ── Student simulator ──────────────────────────────────────────────────────────

PROFILES = {
    "strong": (
        "You are a well-prepared undergraduate student. You have a solid grasp of "
        "the topic, can articulate arguments clearly, cite relevant frameworks, and "
        "engage thoughtfully with counterarguments. Give confident, substantive "
        "answers of 3–5 sentences."
    ),
    "average": (
        "You are an undergraduate student with reasonable but patchy understanding. "
        "You grasp the broad topic but sometimes struggle to go deeper or name "
        "specific frameworks. Your answers are honest but occasionally vague. "
        "Give answers of 2–4 sentences."
    ),
    "weak": (
        "You are an underprepared undergraduate student. Your answers are short, "
        "often generic, and you tend to repeat yourself without engaging with "
        "specifics, or even getting basic facts wrong. Give answers of 1–2 sentences."
    ),
}


def make_student_simulator(profile: str):
    llm = get_llm_settings(cfg)
    name = get_student(cfg)["name"]
    topic = get_assignment(cfg)["topic"]
    desc = PROFILES[profile]

    _api_key = llm.get("api_key")
    client = OpenAI(
        base_url=llm.get("base_url"),
        **({} if _api_key is None else {"api_key": _api_key}),
    )

    def simulate(question: str) -> str:
        if not question:
            return "(no response)"
        try:
            resp = client.chat.completions.create(
                model=llm["model"],
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{desc} Your name is {name} and your assignment was "
                            f"about: {topic}. Respond only with your spoken answer — "
                            "no labels, no preamble, no commentary."
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                max_tokens=200,
                temperature=0.8,
            )
            return resp.choices[0].message.content.strip().strip('"')
        except Exception as exc:
            return f"(simulation error: {exc})"

    return simulate


# ── Transcript writer ──────────────────────────────────────────────────────────


def write_transcript(profile: str, out_path: Path) -> None:
    lines = [
        "=" * 70,
        "  INTERVIEW TEST TRANSCRIPT",
        f"  Profile : {profile}",
        f"  Student : {get_student(cfg)['name']}",
        f"  Topic   : {get_assignment(cfg)['topic']}",
        f"  Date    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
    ]

    for role, text in _log:
        if role == "SESSION":
            lines += ["", "─" * 70, text, "─" * 70, ""]
        elif role == "BOT":
            lines += [f"[BOT] {text}", ""]
        elif role == "STUDENT":
            lines += [f"[STU] {text}", ""]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[test_runner] Transcript saved → {out_path}", flush=True)


# ── Entry point ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Headless interview test runner")
    parser.add_argument(
        "--profile",
        choices=["strong", "average", "weak"],
        default="average",
        help="Simulated student knowledge level (default: average)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Transcript output path (default: tests/test_transcripts/<timestamp>_<profile>.txt)",
    )
    args = parser.parse_args()

    global _stt_fn
    _stt_fn = make_student_simulator(args.profile)

    out_path = (
        Path(args.out)
        if args.out
        else Path(__file__).parent
        / "test_transcripts"
        / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{args.profile}.txt"
    )

    print("=" * 60)
    print("  Interview Bot — Test Runner")
    print(f"  Student profile : {args.profile}")
    print(f"  Output          : {out_path}")
    print("=" * 60)

    import main as interview_main

    try:
        interview_main.main()
    except KeyboardInterrupt:
        print("\n[interrupted]")

    write_transcript(args.profile, out_path)


if __name__ == "__main__":
    main()
