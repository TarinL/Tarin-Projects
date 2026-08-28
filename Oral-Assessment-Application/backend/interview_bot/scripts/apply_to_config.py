"""
apply_to_config.py — Populate interview_config.json from external files.

Two helpers so you don't have to hand-edit interview_config.json:

  1. --submission <file.txt>
     Reads a plain-text student submission and writes it into the
     `student_submission` field, switching the bot into submission mode.

  2. --kb-assessment <file.json>
     Takes the JSON produced by kb_generator.py (knowledge base + a rubric dict
     + a questions list, already in the DB/config shapes) and applies it: sets
     knowledge_base mode, the rubric, and the questions the bot uses at runtime.

Usage:
    python apply_to_config.py --submission submission.txt
    python apply_to_config.py --kb-assessment example_interview.json

Edits interview_config.json in place, preserving its key order and comments.
"""

import argparse
import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "interview_config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def apply_submission(txt_path: str) -> None:
    text = Path(txt_path).read_text(encoding="utf-8").strip()
    if not text:
        sys.exit(f"ERROR: {txt_path} is empty.")

    cfg = _load_config()
    cfg["mode"] = "submission"
    cfg["student_submission"] = text
    _write_config(cfg)

    print(f"Applied submission from {txt_path} ({len(text)} chars).")
    print("  mode -> submission")


def apply_kb_assessment(json_path: str) -> None:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    knowledge_base = (data.get("knowledge_base") or "").strip()
    rubric = data.get("rubric")
    questions = data.get("questions")
    if not knowledge_base:
        sys.exit(f"ERROR: {json_path} has no knowledge_base.")
    # kb_generator now emits the rubric and questions already in the DB/config
    # shapes, so they drop straight in with no reshaping.
    if not isinstance(rubric, dict) or not rubric:
        sys.exit(f"ERROR: {json_path} has no rubric dict.")
    if not isinstance(questions, list) or not questions:
        sys.exit(f"ERROR: {json_path} has no questions list.")

    cfg = _load_config()
    cfg["mode"] = "knowledge_base"
    cfg["knowledge_base"] = knowledge_base
    cfg["assignment"]["rubric"] = rubric
    cfg["questions"] = questions

    _write_config(cfg)

    print(f"Applied KB assessment from {json_path}.")
    print("  mode -> knowledge_base")
    print(f"  rubric criteria: {len(cfg['assignment']['rubric'])}")
    print(f"  questions: {len(cfg['questions'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Populate interview_config.json from a submission .txt or a "
        "kb_generator assessment .json."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--submission", metavar="FILE.txt", help="Plain-text student submission."
    )
    group.add_argument(
        "--kb-assessment",
        metavar="FILE.json",
        help="Assessment JSON produced by kb_generator.py.",
    )
    args = parser.parse_args(argv)

    if args.submission:
        apply_submission(args.submission)
    else:
        apply_kb_assessment(args.kb_assessment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
