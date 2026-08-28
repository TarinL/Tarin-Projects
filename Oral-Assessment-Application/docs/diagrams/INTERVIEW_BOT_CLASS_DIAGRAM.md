# UML class diagram — interview bot

Structure of `backend/interview_bot/`. The bot is mostly **function-based modules** (shown with
the `«module»` stereotype, listing their key public functions) around five real classes:
`InterviewBot`, `InterviewContext`, `InterviewState`, `RecallAudioBridge`, and `RecallClient`.
The prose walkthrough of each module (and the full function lists) is in
[../components/interview-bot.md](../components/interview-bot.md).

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial", "fontSize": "18px"}, "class": {"padding": 10}}}%%
classDiagram
    direction TB

    class trigger["trigger «module»<br/>(container entrypoint)"] {
        +main()
    }

    class session["session «module»"] {
        +run_zoom_interview()
        -_start_ws_gateway()
        -_finish()  -_mark()
    }

    class InterviewBot {
        +ctx: InterviewContext
        +system_prompt
        +time_limit_seconds
        +prefetch_all()
        +run()
        -_step(state)
    }

    class InterviewContext {
        +questions
        +question_index
        +follow_up_depth
        +transcript
        +state: InterviewState
    }

    class InterviewState {
        <<enumeration>>
        INTRO / ASK_QUESTION
        LISTEN / FOLLOW_UP
        NEXT_QUESTION / OPEN_FLOOR
        LISTEN_ADDENDUM
        CLOSE / CLOSE_COMPLETE
        DONE
    }

    class RecallAudioBridge {
        +prefetch(text)
        +speak(text)
        +stream_listen()
    }

    class RecallClient {
        +create_bot()
        +wait_for_join()
        +output_audio()
        +leave_call()
    }

    class zoom_client["zoom_client «module»"] {
        +create_meeting()
        +end_meeting()
    }

    class db_client["db_client «module»"] {
        +get_interview()
        +update_interview()
        +create_zoom()
        +finish_interview()
    }

    class marker["marker «module»"] {
        +mark_interview()
        +call_openai()
        +post_result()
    }

    class prompts["prompts «module»"] {
        +generate_system_prompt()
        +prompt_required_question()
        +prompt_further_q()
    }

    class config["config «module»"] {
        +load_config_from_api()
        +get_student() …
    }

    class audio["audio «module»<br/>(local-mic fallback)"] {
        +text_to_speech()
        +speech_to_text()
    }

    class audio_ws_server["audio_ws_server «module»"] {
        +start()  +get_queue()
    }

    class face_channel["face_channel «module»"] {
        +start()  +set_state()
        +bot_text()  +student_text()
    }

    class notify["notify «module»"] {
        +send_meeting_email()
    }

    trigger --> zoom_client : meeting
    trigger --> db_client : zoom row, status
    trigger --> notify : optional email
    trigger --> session : hands off

    session --> RecallClient : spawns bot
    session --> RecallAudioBridge : creates
    session --> InterviewBot : runs
    session --> face_channel : face feed
    session --> marker : marks
    session --> db_client : write-back

    InterviewBot *-- InterviewContext : owns
    InterviewContext --> InterviewState
    InterviewBot --> prompts : LLM calls
    InterviewBot --> config : settings
    InterviewBot --> audio : speak/listen

    RecallAudioBridge ..|> audio : monkey-patches
    RecallAudioBridge --> RecallClient : MP3 out
    RecallAudioBridge --> audio_ws_server : PCM in

    marker --> db_client : rubric, result
    config --> db_client : INTERVIEW_ID fetch
```

- **`trigger` → `session` → `InterviewBot`** is the production call chain inside the ECS
  container; `main.py` (not shown) is the local headless entrypoint that runs `InterviewBot`
  directly with the `audio` module.
- The dashed realisation from `RecallAudioBridge` to `audio` represents the runtime
  monkey-patch: `session.py` replaces `audio.text_to_speech` / `speech_to_text` with bridge
  methods so the same `InterviewBot` code works over Zoom or a local microphone.

> **Export:** rendered PNG committed alongside (`interview_bot_class_diagram-1.png`). Regenerate with:
> `npx -p @mermaid-js/mermaid-cli mmdc -i INTERVIEW_BOT_CLASS_DIAGRAM.md -o interview_bot_class_diagram.png -w 2000 -s 4 -b transparent`
