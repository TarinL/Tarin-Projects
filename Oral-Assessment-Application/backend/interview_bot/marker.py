"""
marker.py — AI grading module for oral interview assessments.

Currently does:
  1. Fetches the interview record from the API. The rubric is owned by the
     assignment and arrives nested on this record (no separate rubric fetch).
  2. Sends transcript + rubric to OpenAI with a structured grading prompt.
  3. Parses the per-criterion grades + total grade from the response.
  4. POSTs a Result for the interview (POST /api/interview/{id}/result); the
     result shares the interview's id.


Use in interview bot:
  from marker import mark_interview
  result_id = mark_interview(interview_id=42)

API hardcoded for now -> lol
"""

import os
import sys
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# Use the same env var as the rest of the bot (db_client). DB_API_BASE_URL is the
# API host WITHOUT the /api suffix (e.g. http://16.176.4.41:5000); the /api segment
# is appended here, mirroring db_client._url().
API_BASE = os.getenv("DB_API_BASE_URL", "http://16.176.4.41:5000").rstrip("/") + "/api"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Add it to your .env file or export it as an environment variable."
            )
        _client = OpenAI(api_key=api_key)
    return _client


# API Helpers
def _get(path: str) -> dict:
    url = f"{API_BASE}/{path.lstrip('/')}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, payload: dict) -> dict:
    url = f"{API_BASE}/{path.lstrip('/')}"
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return resp.text


def fetch_interview(interview_id: int) -> dict:
    """Return the full InterviewDetail object for the given ID."""
    return _get(f"interview/{interview_id}")


def fetch_rubric(rubric_id: int) -> dict:
    """Return the Rubric object for the given ID."""
    return _get(f"rubric/{rubric_id}")


def post_result(interview_id: int, transcript: str, grade: str, feedback: str) -> int:
    """POST a Result for an interview. The result shares the interview's id, so
    the returned id always equals interview_id."""
    payload = {
        "transcript": transcript,
        "grade": grade,
        "feedback": feedback,
    }
    response = _post(f"interview/{interview_id}/result", payload)
    # The API returns a plain string like "Result added. Result id: 7" (== interview_id)
    if isinstance(response, int):
        return response
    try:
        return int(str(response).split(":")[-1].strip())
    except (ValueError, AttributeError):
        return interview_id


# Grading logic
SYSTEM_PROMPT = """
You are an impartial academic assessor grading an oral interview.
You will be given:
  - A rubric that lists each criterion and the maximum marks available for it.
  - A transcript of the student's interview responses.

Your task:
  1. For EACH criterion in the rubric, award a whole-number score between 0
     and that criterion's maximum marks (inclusive).
  2. Provide one or two sentences of specific feedback per criterion explaining
     the score.
  3. Sum all per-criterion scores to produce a total_score.
  4. Provide 2-3 sentences of overall feedback summarising the student's
     performance.

IMPORTANT — output format:
  Return ONLY valid JSON matching this exact schema, with no extra text,
  no markdown fences, and no commentary outside the JSON:

  {
    "criteria": [
      {
        "criterion": "<name from rubric>",
        "score": <integer awarded>,
        "max_score": <maximum marks for this criterion>,
        "feedback": "<1-2 sentence feedback>"
      }
    ],
    "total_score": <sum of all scores, integer>,
    "total_max": <sum of all max_scores, integer>,
    "overall_feedback": "<2-3 sentence summary>"
  }
""".strip()


def build_user_message(transcript: str, rubric_contents: str) -> str:
    return (
        f"RUBRIC:\n{rubric_contents}\n\n"
        f"INTERVIEW TRANSCRIPT:\n{transcript}"
    )


def call_openai(transcript: str, rubric_contents: str) -> dict:
    """Send transcript + rubric to OpenAI and return parsed grading JSON."""
    client = _get_client()
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,           # low temp for consistent grading
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_message(transcript, rubric_contents),
            },
        ],
    )
    raw = completion.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI returned non-JSON output:\n{raw}") from exc


def format_grade_string(grading: dict) -> str:
    """
    Convert the grading dict to the compact string stored in Result.grade.

    Format:
        <Criterion>: <score>/<max> | ... || TOTAL: <total>/<total_max>
    """
    parts = [
        f"{c['criterion']}: {c['score']}/{c['max_score']}"
        for c in grading.get("criteria", [])
    ]
    total = grading.get("total_score", "?")
    total_max = grading.get("total_max", "?")
    return " | ".join(parts) + f" || TOTAL: {total}/{total_max}"


def format_feedback_string(grading: dict) -> str:
    """
    Convert the grading dict to the compact string stored in Result.feedback.

    Format:
        <Criterion> (<score>/<max>): <feedback>\n...\nOVERALL: <overall_feedback>
    """
    lines = [
        f"{c['criterion']} ({c['score']}/{c['max_score']}): {c['feedback']}"
        for c in grading.get("criteria", [])
    ]
    lines.append(f"OVERALL: {grading.get('overall_feedback', '')}")
    return "\n".join(lines)


# Entry

def mark_interview(interview_id: int, transcript: str | None = None) -> int:
    """
    Full marking pipeline for one interview.

    Parameters
    ----------
    interview_id : int
        The ID of the interview record in the database.
    transcript : str, optional
        Override the transcript fetched from the DB. Used in testing when
        the interview bot has not yet written the transcript to the DB.

    Returns
    -------
    int
        The ID of the newly created Result record.
    """
    print(f"[marker] Fetching interview {interview_id}…")
    interview = fetch_interview(interview_id)

    transcript = transcript or interview.get("transcript") or ""
    if not transcript.strip():
        raise ValueError(
            f"Interview {interview_id} has no transcript. "
            "Run the interview bot first."
        )

    # The rubric is owned by the assignment and arrives nested on the interview
    # record (the API populates it from assignment.rubric_id), so no extra fetch.
    rubric = interview.get("rubric") or {}
    rubric_id = rubric.get("id")
    if rubric_id is None:
        raise ValueError(
            f"Interview {interview_id} has no rubric attached (its assignment has no rubric)."
        )

    rubric_contents = rubric.get("rubricContents", "")
    if not rubric_contents.strip():
        raise ValueError(f"Rubric {rubric_id} is empty.")

    print("[marker] Sending to OpenAI for grading…")
    grading = call_openai(transcript, rubric_contents)

    grade_str = format_grade_string(grading)
    feedback_str = format_feedback_string(grading)

    total = grading.get("total_score", "?")
    total_max = grading.get("total_max", "?")
    print(f"[marker] Score  : {total}/{total_max}")
    print(f"[marker] Grades : {grade_str}")
    print(f"[marker] Storing result…")

    result_id = post_result(
        interview_id=interview_id,
        transcript=transcript,
        grade=grade_str,
        feedback=feedback_str,
    )

    print(f"[marker] Done. Result ID: {result_id}")
    return result_id



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python marker.py <interview_id>")
        sys.exit(1)
    try:
        iid = int(sys.argv[1])
    except ValueError:
        print(f"Error: interview_id must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)
    mark_interview(iid)
