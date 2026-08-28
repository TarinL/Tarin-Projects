"""
bot.py — Interview state machine.

Student details, assignment info, and the system prompt are now derived
entirely from interview_config.json via config.py — no more hardcoded
file paths or txt files.
"""

import time

from context import InterviewState, InterviewContext
from config import (
    cfg,
    get_student,
    get_assignment,
    get_interview_settings,
    get_questions,
)
from prompts import (
    generate_system_prompt,
    generate_closing_script,
    generate_closing_script_complete,
    prompt_open_floor,
    prompt_further_q,
    prompt_required_question,
    determine_follow_up_depth,
)
import audio


class InterviewBot:
    def __init__(self, config: dict = cfg):
        self.config = config
        self.student_details = get_student(config)
        self.assignment_details = get_assignment(config)
        interview = get_interview_settings(config)

        self.time_limit_seconds: int = interview["duration_minutes"] * 60
        self.closing_buffer_seconds: int = interview.get("closing_buffer_seconds", 0)
        self.max_follow_up_depth: int = interview["follow_up_depth"]
        self.warning_seconds_remaining: int = interview.get(
            "warning_seconds_remaining", 0
        )

        self.system_prompt = generate_system_prompt(config)
        self.ctx = InterviewContext(
            questions=get_questions(config),
            follow_up_depth=self.max_follow_up_depth,
        )
        self._halfway_warned = False
        self._question_text_cache: dict[int, str] = {}
        self._phrase_cache: dict[str, str] = {}  # 'closing' | 'closing_complete' | 'open_floor'

    def prefetch_all(self) -> None:
        """Pre-generate all deterministic LLM text in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        questions = self.ctx.questions
        n_total = len(questions) + 3
        print(f"[bot] Pre-generating {n_total} LLM items in parallel…", flush=True)

        with ThreadPoolExecutor(max_workers=n_total) as executor:
            # questions: key = int index
            futures: dict = {
                executor.submit(prompt_required_question, q, self.system_prompt, i == 0, self.config): i
                for i, q in enumerate(questions)
            }
            # static phrases: key = str name
            futures[executor.submit(generate_closing_script, self.config)] = "closing"
            futures[executor.submit(generate_closing_script_complete, self.config)] = "closing_complete"
            futures[executor.submit(prompt_open_floor, self.config)] = "open_floor"

            for future in as_completed(futures):
                key = futures[future]
                try:
                    text = future.result()
                    if isinstance(key, int):
                        self._question_text_cache[key] = text
                    else:
                        self._phrase_cache[key] = text
                except Exception as exc:
                    print(f"[bot] Warning: failed to prefetch {key!r}: {exc}", flush=True)

        n_cached = len(self._question_text_cache) + len(self._phrase_cache)
        print(f"[bot] Cached {n_cached}/{n_total} items.", flush=True)

    # ── Timer helpers ──────────────────────────────────────────────────────────

    def _time_elapsed(self) -> int:
        """Seconds elapsed since the interview started (0 if not yet started)."""
        if self.ctx.start_time is None:
            return 0
        return int(time.time() - self.ctx.start_time)

    def _time_is_up(self) -> bool:
        return self._time_elapsed() >= self.time_limit_seconds

    def _play_warning_if_due(self) -> None:
        if self.warning_seconds_remaining <= 0 or self._halfway_warned:
            return
        warn_at = self.time_limit_seconds - self.warning_seconds_remaining
        if self._time_elapsed() < warn_at:
            return
        self._halfway_warned = True
        secs = self.warning_seconds_remaining
        if secs >= 60 and secs % 60 == 0:
            time_str = f"{secs // 60} minutes"
        elif secs >= 60:
            time_str = f"{secs // 60} minutes and {secs % 60} seconds"
        else:
            time_str = f"{secs} seconds"
        audio.text_to_speech(
            f"Please note that we have {time_str} remaining in this interview. "
            "Please keep your responses concise."
        )

    def _compute_dynamic_depth(self) -> int:
        """Calculate follow-up depth for the current question based on time elapsed."""
        questions_remaining = self.ctx.questions[self.ctx.question_index :]
        if not questions_remaining:
            return 0
        depth = determine_follow_up_depth(
            time_limit=self.time_limit_seconds,
            questions_remaining=questions_remaining,
            time_remaining=self._time_elapsed(),
            config=self.config,
        )
        return min(depth, self.max_follow_up_depth)

    # ── State machine ──────────────────────────────────────────────────────────

    def run(self):
        while self.ctx.state != InterviewState.DONE:
            self.ctx.state = self._step(self.ctx.state)

    def _step(self, state: InterviewState) -> InterviewState:
        match state:
            case InterviewState.INTRO:
                student_name = self.student_details["name"]
                ready_prompt = (
                    f'Hello {student_name}, say "Ready to begin" whenever '
                    "you're ready to start the interview."
                )
                while True:
                    audio.text_to_speech(ready_prompt)
                    response = audio.speech_to_text(timeout=30)
                    if "ready" in response.lower():
                        break
                    print("[bot] No ready signal — repeating prompt.", flush=True)
                self.ctx.start_time = time.time()
                audio.set_interview_start()
                print("\n[Interview started: {}]".format(time.ctime()))
                return InterviewState.ASK_QUESTION

            case InterviewState.ASK_QUESTION:
                if self._time_is_up():
                    return InterviewState.CLOSE

                self._play_warning_if_due()
                self.ctx.follow_up_depth = self._compute_dynamic_depth()

                q = self.ctx.questions[self.ctx.question_index]
                question_text = self._question_text_cache.pop(
                    self.ctx.question_index, None
                )
                if question_text is None:
                    question_text = prompt_required_question(
                        question=q,
                        system_prompt=self.system_prompt,
                        first_question=self.ctx.is_first_question,
                        config=self.config,
                    )
                audio.text_to_speech(question_text)
                self.ctx.current_question_text = question_text
                self.ctx.is_first_question = False
                self.ctx.follow_up_count = 0
                self.ctx.session_transcript = []  # fresh context window per required question
                return InterviewState.LISTEN

            case InterviewState.LISTEN:
                self.ctx.last_response = audio.speech_to_text()
                entry = {
                    "question_index": self.ctx.question_index,
                    "area_of_focus": self.ctx.questions[self.ctx.question_index][0],
                    "question": self.ctx.current_question_text,
                    "response": self.ctx.last_response,
                }
                self.ctx.transcript.append(entry)
                self.ctx.session_transcript.append(entry)
                if self._time_is_up():
                    return InterviewState.CLOSE
                if self.ctx.follow_up_count < self.ctx.follow_up_depth:
                    return InterviewState.FOLLOW_UP
                return InterviewState.NEXT_QUESTION

            case InterviewState.FOLLOW_UP:
                follow_up_q = prompt_further_q(
                    last_response=self.ctx.last_response,
                    session_transcript=self.ctx.session_transcript,
                    config=self.config,
                    timestamp=str(self.ctx.follow_up_count),
                )
                audio.text_to_speech(follow_up_q)
                self.ctx.current_question_text = follow_up_q
                self.ctx.follow_up_count += 1
                return InterviewState.LISTEN

            case InterviewState.NEXT_QUESTION:
                self.ctx.question_index += 1
                if self.ctx.question_index >= len(self.ctx.questions):
                    if self._time_is_up():
                        return InterviewState.CLOSE
                    return InterviewState.OPEN_FLOOR
                if self._time_is_up():
                    return InterviewState.CLOSE
                return InterviewState.ASK_QUESTION

            case InterviewState.OPEN_FLOOR:
                question_text = self._phrase_cache.pop("open_floor", None) or prompt_open_floor(self.config)
                audio.text_to_speech(question_text)
                self.ctx.current_question_text = question_text
                return InterviewState.LISTEN_ADDENDUM

            case InterviewState.LISTEN_ADDENDUM:
                response = audio.speech_to_text()
                self.ctx.transcript.append(
                    {
                        "question_index": None,
                        "area_of_focus": "Open floor",
                        "question": self.ctx.current_question_text,
                        "response": response,
                    }
                )
                return InterviewState.CLOSE_COMPLETE

            case InterviewState.CLOSE:
                script = self._phrase_cache.pop("closing", None) or generate_closing_script(self.config)
                audio.text_to_speech(script)
                return InterviewState.DONE

            case InterviewState.CLOSE_COMPLETE:
                script = self._phrase_cache.pop("closing_complete", None) or generate_closing_script_complete(self.config)
                audio.text_to_speech(script)
                return InterviewState.DONE
