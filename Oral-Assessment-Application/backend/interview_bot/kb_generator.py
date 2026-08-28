"""
kb_generator.py — Stage-1 generator for knowledge-base ('flipped classroom')
formative assessments.

Given a plain-text knowledge base (the required readings/notes) and a desired
number of lines of questioning, this produces an editable JSON artifact for the
instructor: a rubric (generated if not supplied) plus a set of lines of
questioning / areas of focus that test whether students engaged with and
understood the material.

This is deliberately a standalone, instructor-side tool: no DB or API calls. It
reuses the project's LLM settings from interview_config.json (model, base_url,
api_key) via config.py, and uses OpenAI JSON mode for structured output — the
pattern proven in marker.py.

CLI:
    python kb_generator.py <knowledge_base.txt> \\
        --num-questions N \\
        [--rubric rubric.json|rubric.txt] \\
        [--out output.json] \\
        [--model gpt-4o]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from config import cfg, get_llm_settings


# ── LLM client (config-driven, JSON mode) ────────────────────────────────────

_llm = get_llm_settings(cfg)
_api_key = _llm.get("api_key")
_client = OpenAI(
    base_url=_llm.get("base_url"),
    **({} if _api_key is None else {"api_key": _api_key}),
)
DEFAULT_MODEL: str = _llm["model"]


def _json_call(messages: list[dict], model: str) -> dict:
    """Call the chat completion API in JSON mode and return the parsed object."""
    completion = _client.chat.completions.create(
        model=model,
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=messages,
    )
    raw = completion.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON output:\n{raw}") from exc


# ── Rubric ───────────────────────────────────────────────────────────────────

_RUBRIC_SHAPE = (
    'Return JSON of the form {"rubric": [{"criterion": "<short name>", '
    '"description": "<one or two sentences>", "weight": <integer>}]}. '
    "Weights must be positive integers that sum to exactly 100."
)


def generate_rubric(knowledge_base: str, model: str) -> list[dict]:
    """Generate a formative rubric (4-6 criteria, weights summing to 100)."""
    system = (
        "You design concise rubrics for LIGHT, FORMATIVE oral checks in a "
        "flipped-classroom setting. The aim is to gauge whether a student has "
        "done the required reading and understood the key ideas — not to conduct "
        "a rigorous summative exam. Favour comprehension and retention over deep "
        "critique. Produce between 4 and 6 criteria. " + _RUBRIC_SHAPE
    )
    user = (
        "Design a rubric for assessing student understanding of the following "
        "course material:\n\n"
        "--- BEGIN KNOWLEDGE BASE ---\n"
        f"{knowledge_base}\n"
        "--- END KNOWLEDGE BASE ---"
    )
    data = _json_call(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model,
    )
    return _coerce_rubric(data)


def normalize_rubric(raw: str, model: str) -> list[dict]:
    """Coerce an instructor-supplied rubric into the standard schema.

    If `raw` is valid JSON already matching the shape, it is passed through
    unchanged. Otherwise (plain text) a single LLM call restructures it into the
    {criterion, description, weight} list so downstream marking stays
    per-criterion compatible.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    if parsed is not None:
        return _coerce_rubric(parsed)

    system = (
        "You convert a free-text rubric into structured JSON without changing "
        "its meaning. " + _RUBRIC_SHAPE + " If the source omits weights, "
        "distribute them sensibly so they still sum to 100."
    )
    data = _json_call(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Rubric to structure:\n\n{raw}"},
        ],
        model,
    )
    return _coerce_rubric(data)


def _coerce_rubric(data) -> list[dict]:
    """Extract and validate the rubric list from a parsed JSON value."""
    if isinstance(data, dict):
        items = data.get("rubric", data.get("criteria"))
    else:
        items = data
    if not isinstance(items, list) or not items:
        raise ValueError(f"Could not find a rubric list in: {data!r}")

    rubric = []
    for item in items:
        rubric.append(
            {
                "criterion": str(item["criterion"]),
                "description": str(item.get("description", "")),
                "weight": int(item["weight"]),
            }
        )
    return rubric


# ── Lines of questioning ──────────────────────────────────────────────────────


def generate_questions(knowledge_base: str, num: int, model: str) -> list[dict]:
    """Generate `num` questions grounded in the KB, already in the DB/bot shape.

    Returns a list of {"text", "weight"} dicts — the exact shape stored in the
    assignment.questions column (and read by config.get_questions). Each entry is
    an area of focus, not a script: at runtime the interview bot (which also has
    the full knowledge base) turns the guidance text into its own spoken question,
    so wording can vary per student to deter cheating. `weight` is the relative
    importance of the area; weights sum to 100.
    """
    system = (
        "You design lines of questioning for a LIGHT, FORMATIVE oral check in a "
        "flipped-classroom setting. Each entry is an AREA OF FOCUS that an "
        "interview bot will later turn into its own spoken question at runtime; "
        "the bot has the full knowledge base available and will phrase the "
        "question itself (and vary it per student to deter cheating). Your job "
        "is to tell the bot precisely WHERE to aim, not to write the question. "
        "The goal is to surface whether the student actually engaged with the "
        "material and understands it, including light application — not just "
        "recall. "
        f"Produce EXACTLY {num} distinct areas of focus that together give "
        "good coverage of the material. Make them SPECIFIC and granular — anchor "
        "each one to a concrete concept, claim, mechanism, or example drawn "
        "directly from the knowledge base. Do NOT mirror broad assessment "
        "categories or rubric-style headings; these areas of focus are meant to "
        "be more pointed than that. "
        'Return JSON of the form {"questions": [{"text": "<a single '
        "self-contained guidance string for the bot that names the focus area, "
        "explains why probing it reveals genuine understanding, and describes the "
        "specific angle/sub-topic to hone in on — guidance for the bot, NOT a "
        'question to read aloud>", "weight": <integer>}]}. The weight is the '
        "relative importance of this area; weights must be positive integers that "
        "sum to exactly 100."
    )
    user = (
        "Course material:\n"
        "--- BEGIN KNOWLEDGE BASE ---\n"
        f"{knowledge_base}\n"
        "--- END KNOWLEDGE BASE ---"
    )
    data = _json_call(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model,
    )
    items = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ValueError(f"Could not find questions in: {data!r}")

    questions = []
    for item in items:
        questions.append(
            {
                "text": str(item["text"]),
                "weight": int(item["weight"]),
            }
        )
    # Models occasionally over- or under-produce for small counts; enforce the
    # requested number deterministically rather than trusting the model.
    return questions[:num]


# ── Orchestration ─────────────────────────────────────────────────────────────


def generate_assessment(
    knowledge_base: str,
    num_questions: int,
    rubric_input: str | None = None,
    model: str | None = None,
) -> dict:
    """Build the full standalone assessment artifact."""
    model = model or DEFAULT_MODEL
    knowledge_base = knowledge_base.strip()
    if not knowledge_base:
        raise ValueError("Knowledge base is empty.")
    if num_questions < 1:
        raise ValueError("num_questions must be at least 1.")

    rubric_provided = rubric_input is not None
    if rubric_provided:
        rubric = normalize_rubric(rubric_input, model)
    else:
        rubric = generate_rubric(knowledge_base, model)

    # Emit the rubric as the criterion-keyed dict stored in rubric.rubricContents,
    # so seed_interview.py serializes it straight into the DB with no reshaping.
    rubric_dict = {
        c["criterion"]: {"description": c["description"], "weight": c["weight"]}
        for c in rubric
    }

    questions = generate_questions(knowledge_base, num_questions, model)

    return {
        "mode": "knowledge_base",
        "knowledge_base": knowledge_base,
        "rubric": rubric_dict,
        "questions": questions,
        "_meta": {
            "model": model,
            "num_questions_requested": num_questions,
            "rubric_provided": rubric_provided,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── CLI ────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a knowledge-base formative assessment (rubric + "
        "lines of questioning) for instructor review."
    )
    parser.add_argument(
        "knowledge_base", help="Path to a plain-text knowledge base file."
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        required=True,
        help="Number of lines of questioning / areas of focus to generate.",
    )
    parser.add_argument(
        "--rubric",
        help="Optional path to an existing rubric (.json in the schema, or .txt "
        "free text to be structured).",
    )
    parser.add_argument(
        "--out",
        help="Path to write the output JSON. Defaults to stdout.",
    )
    parser.add_argument(
        "--model",
        help=f"LLM model override. Defaults to the config model ({DEFAULT_MODEL}).",
    )
    args = parser.parse_args(argv)

    knowledge_base = Path(args.knowledge_base).read_text(encoding="utf-8")
    rubric_input = (
        Path(args.rubric).read_text(encoding="utf-8") if args.rubric else None
    )

    result = generate_assessment(
        knowledge_base=knowledge_base,
        num_questions=args.num_questions,
        rubric_input=rubric_input,
        model=args.model,
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        print(f"[kb_generator] Wrote {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
