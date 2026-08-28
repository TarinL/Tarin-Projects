"""
transcript_format.py — Shared transcript rendering.

Renders interview transcript entries (as produced by InterviewBot.ctx.transcript)
grouped by area-of-focus section. Each section leads with a header, then lists the
actual questions the bot asked ([BOT]) and the student's answers ([STU]) — including
follow-ups, which share their parent question's index and so fall under the same
section.

Entry shape (see bot.py):
    {
        "question_index": int | None,   # None => open floor
        "area_of_focus": str,           # section header text
        "question": str,                # the actual question the bot spoke
        "response": str,                # the student's answer
    }
"""


def format_transcript(entries: list[dict]) -> str:
    """Return a section-grouped, [BOT]/[STU]-labelled transcript string."""
    lines: list[str] = []
    current = object()  # sentinel so the first entry always opens a new section
    for e in entries:
        qi = e.get("question_index")
        if qi != current:
            current = qi
            if lines:
                lines.append("")
            header = (
                "Open floor"
                if qi is None
                else f"Section {qi + 1}: {e.get('area_of_focus', '')}"
            )
            lines += [header, ""]
        lines += [
            f"[BOT] {e.get('question', '')}",
            "",
            f"[STU] {e.get('response', '')}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"
