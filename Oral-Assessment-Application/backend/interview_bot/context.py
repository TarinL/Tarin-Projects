from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class InterviewState(Enum):
    INTRO = auto()
    ASK_QUESTION = auto()
    LISTEN = auto()
    FOLLOW_UP = auto()
    NEXT_QUESTION = auto()
    OPEN_FLOOR = auto()       # all questions done within time — ask if anything to add
    LISTEN_ADDENDUM = auto()  # capture the student's addendum response
    CLOSE = auto()            # time ran out
    CLOSE_COMPLETE = auto()   # finished all questions within time
    DONE = auto()


@dataclass
class InterviewContext:
    questions: list[str]
    question_index: int = 0
    follow_up_depth: int = 2  # current (dynamic) follow-up depth for active question
    follow_up_count: int = 0
    transcript: list[dict] = field(default_factory=list)
    session_transcript: list[dict] = field(default_factory=list)  # resets per required question
    last_response: Optional[str] = None
    current_question_text: Optional[str] = None  # the actual question last spoken by the bot
    state: InterviewState = InterviewState.INTRO
    is_first_question: bool = True
    start_time: Optional[float] = None  # set when interview begins (time.time())
