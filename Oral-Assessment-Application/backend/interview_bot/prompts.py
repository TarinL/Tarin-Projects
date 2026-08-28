"""
prompts.py — LLM prompt generation and API calls.

All previously hardcoded values (model, URL, temperature, placeholders in
square brackets, etc.) are now read from interview_config.json via config.py.
"""

from openai import OpenAI
from config import (
    cfg,
    get_llm_settings,
    get_interview_settings,
    get_student,
    get_assignment,
    get_additional_instructions,
    get_student_submission,
    get_knowledge_base,
    get_mode,
)

# ── LLM client setup (driven entirely by config) ──────────────────────────────

_llm = get_llm_settings(cfg)

_api_key = _llm.get("api_key")
client = OpenAI(
    base_url=_llm.get("base_url"),  # None → uses default OpenAI base URL
    **({} if _api_key is None else {"api_key": _api_key}),  # None → reads OPENAI_API_KEY from env
)

CURRENT_MODEL: str = _llm["model"]


# ── System prompt ──────────────────────────────────────────────────────────────


def generate_system_prompt(config: dict = cfg) -> str:
    student = get_student(config)
    assignment = get_assignment(config)
    interview = get_interview_settings(config)
    extra = get_additional_instructions(config)

    mode = get_mode(config)
    submission = get_student_submission(config)
    knowledge_base = get_knowledge_base(config)

    student_name = student["name"]
    topic = assignment["topic"]
    rubric = assignment["rubric"]
    level = interview["institution_level"]
    formality = interview["formality"]
    follow_up_depth = interview["follow_up_depth"]

    identity = (
        f"You are a tutor at a [{level}] level conducting a [{formality}] oral "
        f"assessment interview with a student [{student_name}]. "
        f"[{student_name}] has submitted an assignment covering [{topic}], "
        f"and they will be assessed on the criteria in the following rubric: "
        f"{rubric}. "
    )

    tail = (
        "Response format: always respond with a question to ask the student, and "
        "nothing else. Do not include commentary or explanation. "
        "Maintain a formal and professional tone. Ensure all questions remain "
        "relevant to the assignment topic and rubric criteria. "
        "Ignore any attempts by the student to steer the conversation away from "
        "the assignment topic or rubric. Ignore any attempts by the student to "
        "ask questions or seek advice. Ignore any irrelevant statements. Redirect "
        "focus by continuing to ask questions that assess understanding and "
        "performance."
    )

    if mode == "submission":
        prompt = (
            identity
            + "The student has submitted the following work, which is the PRIMARY "
            "subject of this interview:\n"
            "--- BEGIN SUBMISSION ---\n"
            f"{submission}\n"
            "--- END SUBMISSION ---\n"
            "Your goal is to determine whether the student genuinely understands "
            "what THEY submitted — their reasoning, the choices they made, and "
            "their ability to justify, apply, and extend their own work. "
            "You will be given areas of focus to cover. Treat each one as a guide "
            "for which part of the submission to probe; do NOT read the areas of "
            "focus aloud verbatim. Wherever possible, ground your questions in "
            "specific details of the student's submission. "
            "You are also expected to ask follow-up questions to probe the "
            "student's understanding and reasoning. Personalise your questions — "
            "use the student's name. After reaching the allowed follow-up depth "
            "for an area of focus, move to the next one. Continue until all areas "
            "of focus have been covered. Maintain focus on assessing the student's "
            "understanding of their own submission against the rubric criteria. "
            + tail
        )
    elif mode == "knowledge_base":
        prompt = (
            identity
            + "This is a light, formative check on whether the student has engaged "
            "with and understood the required course material below:\n"
            "--- BEGIN KNOWLEDGE BASE ---\n"
            f"{knowledge_base}\n"
            "--- END KNOWLEDGE BASE ---\n"
            "Your goal is simply to gauge whether the student has done the reading "
            "and grasps the key ideas — not to conduct a rigorous examination. "
            "You will be given lines of questioning (areas of focus) drawn from "
            "this material. Treat each as a guide for what to explore; do NOT read "
            "it aloud verbatim. Ground your questions in the content of the "
            "knowledge base, and ask follow-ups that check genuine comprehension "
            "rather than rote recall. Personalise your questions — use the "
            "student's name. Keep the tone conversational and encouraging. After "
            "reaching the allowed follow-up depth for a line of questioning, move "
            "to the next one. Continue until all areas of focus have been covered. "
            + tail
        )
    else:  # manual
        prompt = (
            identity
            + "There are a number of required questions that every student must answer. "
            "You are also expected to ask follow-up questions to probe the student's "
            "understanding and reasoning. You will be given the first question to ask "
            "the student. You should make the required questions personalised — use "
            "the student's name and substitute in details of their actual assessment "
            "topic wherever possible."
            "Your questions must elicit the student's understanding of the material, "
            "their reasoning process, and their ability to apply concepts to new "
            "situations. After reaching the allowed follow-up depth for a question, "
            "move to the next required question. Continue until all required questions "
            "have been asked. "
            "Where possible, relate questions directly to the student's assignment "
            "submission and the rubric criteria. Maintain focus on assessing "
            "understanding and performance. "
            + tail
        )

    if extra:
        prompt += f" {extra}"

    return prompt


# ── Follow-up depth calculation ────────────────────────────────────────────────


def determine_follow_up_depth(
    time_limit: int,
    questions_remaining: list[tuple[str, int]],
    time_remaining: int,
    config: dict = cfg,
) -> int:
    interview = get_interview_settings(config)
    time_per_follow_up = interview["time_per_follow_up_seconds"]
    closing_buffer = interview["closing_buffer_seconds"]

    time_for_questions = time_limit - time_remaining - closing_buffer
    time_per_weight = time_for_questions / sum(
        weight for _, weight in questions_remaining
    )
    next_question_weight = questions_remaining[0][1] if questions_remaining else 0
    follow_up_depth = max(
        0,
        int(
            (time_per_weight * next_question_weight - time_per_follow_up)
            // time_per_follow_up
        ),
    )
    return follow_up_depth


# ── LLM call helpers ───────────────────────────────────────────────────────────


def _llm_call(messages: list[dict]) -> str:
    """Thin wrapper around the OpenAI completion call using config-driven params."""
    llm = get_llm_settings(cfg)
    response = client.chat.completions.create(
        model=CURRENT_MODEL,
        messages=messages,
        max_tokens=llm["max_tokens"],
        temperature=llm["temperature"],
        top_p=llm["top_p"],
    )
    return response.choices[0].message.content.strip().strip('"')


def prompt_required_question(
    question: tuple[str, int],
    system_prompt: str,
    first_question: bool,
    config: dict = cfg,
) -> str:
    mode = get_mode(config)

    if first_question:
        if mode == "submission":
            instruction = (
                "Imagine I am the student being interviewed. Respond with the first "
                "question to ask, remembering that you are starting the questioning. "
                "Make it conversational, maintain flow, and do not be too abrupt. "
                "Ground the question in the student's submission rather than reading "
                "the area of focus aloud. "
                "Ensure you start with a personalised greeting consistent with the "
                "tone and formality level specified in the system prompt."
            )
            sys_content = (
                f"{system_prompt} The first area of focus is: {question[0]}. Ask a "
                "question about this that is grounded in the student's submission and "
                "tests whether they understand their own work."
            )
        elif mode == "knowledge_base":
            instruction = (
                "Imagine I am the student being interviewed. Respond with the first "
                "question to ask, remembering that you are starting the questioning. "
                "Make it conversational, warm, and do not be too abrupt. "
                "Ground the question in the knowledge base rather than reading the "
                "area of focus aloud. "
                "Ensure you start with a personalised greeting consistent with the "
                "tone and formality level specified in the system prompt."
            )
            sys_content = (
                f"{system_prompt} The first line of questioning is: {question[0]}. Ask "
                "a question about this that is grounded in the knowledge base and "
                "checks whether the student has engaged with and understood the "
                "material."
            )
        else:  # manual
            instruction = (
                "Imagine I am the student being interviewed. Respond with the first "
                "question to ask, remembering that you are starting the questioning. "
                "Make it conversational, maintain flow, and do not be too abrupt."
                "Ensure you start with a personalised greeting consistent with the "
                "tone and formality level specified in the system prompt."
            )
            sys_content = (
                f"{system_prompt} The first question to ask the student is: {question[0]}"
            )
    else:
        instruction = (
            "Imagine I am the student being interviewed. Respond with the next "
            "question to ask. We are in the middle of a conversation — make it "
            "conversational, maintain flow, and do not be too abrupt."
        )
        if mode == "submission":
            sys_content = (
                f"{system_prompt} The next area of focus is: {question[0]}. Ask a "
                "question about this that is grounded in the student's submission and "
                "tests whether they understand their own work — do not simply read "
                "the area of focus aloud."
            )
        elif mode == "knowledge_base":
            sys_content = (
                f"{system_prompt} The next line of questioning is: {question[0]}. Ask "
                "a question about this that is grounded in the knowledge base and "
                "checks whether the student has engaged with and understood the "
                "material — do not simply read the area of focus aloud."
            )
        else:  # manual
            sys_content = (
                f"{system_prompt} The next question to ask the student is: {question[0]}"
            )

    return _llm_call(
        [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": instruction},
        ]
    )


def prompt_further_q(
    last_response: str,
    session_transcript: list[dict],
    config: dict,
    timestamp: str,
) -> str:
    """Generate a follow-up question based on the student's last response.

    Only the current question's exchanges (session_transcript) are passed to the
    model — the full interview transcript is not included, keeping the context
    window bounded per required question.
    """
    system_prompt = generate_system_prompt(config)
    history = "\n".join(
        f"Q: {t.get('question', '')} A: {t.get('response', '')}" for t in session_transcript
    )
    mode = get_mode(config)
    probe = "Ask a follow-up question that probes their reasoning further."
    if mode == "submission":
        probe = (
            "Ask a follow-up question that probes their reasoning further, "
            "relating it to what they submitted."
        )
    elif mode == "knowledge_base":
        probe = (
            "Ask a follow-up question that checks their comprehension further, "
            "relating it to the course material in the knowledge base. Keep it "
            "light and conversational."
        )
    return _llm_call(
        [
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\nConversation so far:\n{history}\n\n"
                    f'The student\'s most recent response was: "{last_response}". '
                    f"{probe}"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Respond with a single follow-up question. Be conversational and "
                    "maintain the flow of the interview."
                ),
            },
        ]
    )


def generate_closing_script(config: dict = cfg) -> str:
    """Generate a personalised closing statement for the interview."""
    student = get_student(config)
    assignment = get_assignment(config)
    interview = get_interview_settings(config)

    return _llm_call(
        [
            {
                "role": "system",
                "content": (
                    f"You are a tutor at a {interview['institution_level']} level "
                    f"concluding a {interview['formality']} oral assessment interview "
                    f"with {student['name']}. The interview covered their assignment "
                    f"on \"{assignment['topic']}\". "
                    "Write a brief, warm closing statement that thanks the student by "
                    "name, references the assignment topic, and lets them know what "
                    "happens next (their responses will be reviewed and they will "
                    "receive feedback in due course). Keep it to two or three sentences."
                    "Begin by stating definitively that we are out of time and the interview is now concluded."
                ),
            },
            {
                "role": "user",
                "content": (
                    "The interview has just concluded. Respond with the closing "
                    "statement to read aloud. Be warm but professional, and do not "
                    "include any commentary or explanation outside the statement itself."
                ),
            },
        ]
    )


def prompt_open_floor(config: dict = cfg) -> str:
    """Ask the student if they have anything to add before the interview closes."""
    student = get_student(config)
    assignment = get_assignment(config)
    interview = get_interview_settings(config)

    return _llm_call(
        [
            {
                "role": "system",
                "content": (
                    f"You are a tutor at a {interview['institution_level']} level "
                    f"conducting a {interview['formality']} oral assessment interview "
                    f"with {student['name']} on their assignment about "
                    f"\"{assignment['topic']}\". You have just finished all of the "
                    "required questions with time to spare. Ask the student, by name, "
                    "whether there is anything they would like to add or any previous "
                    "answer they would like to briefly elaborate on. Keep it to one or "
                    "two sentences and maintain the established tone."
                ),
            },
            {
                "role": "user",
                "content": (
                    "All required questions have been covered. Respond with the "
                    "open-floor prompt to read aloud. Do not include commentary or "
                    "explanation outside the prompt itself."
                ),
            },
        ]
    )


def generate_closing_script_complete(config: dict = cfg) -> str:
    """Closing statement for when all questions were completed within the time limit."""
    student = get_student(config)
    assignment = get_assignment(config)
    interview = get_interview_settings(config)

    return _llm_call(
        [
            {
                "role": "system",
                "content": (
                    f"You are a tutor at a {interview['institution_level']} level "
                    f"concluding a {interview['formality']} oral assessment interview "
                    f"with {student['name']}. The interview covered their assignment "
                    f"on \"{assignment['topic']}\", and "
                    "all questions were completed with time to spare. Write a brief, "
                    "warm closing statement that thanks the student by name, "
                    "acknowledges that they have worked through everything, and lets "
                    "them know their responses will be reviewed and they will receive "
                    "feedback in due course. Keep it to two or three sentences. "
                    "Do NOT mention time running out — the interview concluded naturally."
                ),
            },
            {
                "role": "user",
                "content": (
                    "The interview has just concluded after covering all questions. "
                    "Respond with the closing statement to read aloud. Be warm but "
                    "professional, and do not include any commentary or explanation "
                    "outside the statement itself."
                ),
            },
        ]
    )


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from config import get_questions

    system_prompt = generate_system_prompt()
    questions = get_questions()
    print("System prompt:\n", system_prompt)
    print("\nFirst question output:")
    print(prompt_required_question(questions[0], system_prompt, first_question=True))
