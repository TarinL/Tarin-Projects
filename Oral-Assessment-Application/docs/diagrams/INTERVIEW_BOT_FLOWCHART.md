# Interview Bot — End-to-End Flowchart (per-phase, left-to-right)

One interview, traced from the frontend "start" click through to marking.
Worked example: **5 lines of questioning**, **follow-up depth = 2**.

**Presentation note:** each phase below is its **own standalone diagram that flows
strictly left → right**, sized for **one phase per slide**. Concurrency is shown as
**parallel horizontal branches** (a fork splits into two rows that both run rightward
and rejoin) — so anything stacked vertically *within a phase* is running at the same time.

Legend (by box colour) — blue = our code · green = our DB (via the .NET API) ·
purple = AWS infra · orange = external paid API. Dashed edges = loop-backs.

---

## Overview rail

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 45, "nodeSpacing": 32, "padding": 14}}}%%
flowchart TB
    classDef p1 fill:#dbeafe,stroke:#2563eb,color:#0b2447,stroke-width:2px;
    classDef p2 fill:#e0e7ff,stroke:#4f46e5,color:#1e1b4b,stroke-width:2px;
    classDef p3 fill:#ede9fe,stroke:#7c3aed,color:#2e1065,stroke-width:2px;
    classDef p4 fill:#fae8ff,stroke:#c026d3,color:#4a044e,stroke-width:2px;
    classDef p5 fill:#fce7f3,stroke:#db2777,color:#500724,stroke-width:2px;
    classDef p6 fill:#ffe4e6,stroke:#e11d48,color:#4c0519,stroke-width:2px;
    classDef p7 fill:#ffedd5,stroke:#ea580c,color:#431407,stroke-width:2px;
    classDef p8 fill:#fef9c3,stroke:#ca8a04,color:#422006,stroke-width:2px;
    classDef p9 fill:#dcfce7,stroke:#16a34a,color:#052e16,stroke-width:2px;

    subgraph ROW1[" Setup &amp; join "]
        direction LR
        P1["▶️ Phase 1<br/><b>Trigger</b>"]:::p1 --> P2["📦 Phase 2<br/><b>ECS boot</b>"]:::p2 --> P3["🎥 Phase 3<br/><b>Meeting setup</b>"]:::p3 --> P4["⚙️ Phase 4<br/><b>Session init</b><br/>(parallel)"]:::p4 --> P5["👋 Phase 5<br/><b>Intro</b>"]:::p5
    end

    subgraph ROW2[" Interview → results "]
        direction LR
        P6["❓ Phase 6<br/><b>Question loop</b><br/>*X · follow-up *Y"]:::p6 --> P7["🏁 Phase 7<br/><b>Wrap-up</b>"]:::p7 --> P8["🧹 Phase 8<br/><b>End procedure</b>"]:::p8 --> P9["📝 Phase 9<br/><b>Marking</b>"]:::p9
    end

    ROW1 == "continues ⤵" ==> ROW2

    style ROW1 fill:transparent,stroke:#cbd5e1,stroke-width:1px,color:#334155;
    style ROW2 fill:transparent,stroke:#cbd5e1,stroke-width:1px,color:#334155;
```

---

## Phase 1 — Trigger (synchronous; returns immediately)

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    FE1["Frontend<br/>POST /api/interview/&#123;id&#125;/start"]:::ours
    A2[".NET API<br/>load interview row"]:::ours
    D2["RDS<br/>SELECT interview"]:::db
    A3[".NET API<br/>ecs.RunTask Fargate<br/>(override INTERVIEW_ID)"]:::ours
    ACK["return &#123;status:starting&#125;<br/>to frontend"]:::ours
    NEXT["→ Phase 2<br/>(task starts async)"]:::ours

    FE1 --> A2
    A2 --> D2
    A2 --> A3
    A3 --> ACK
    A3 -. "async (out-of-band)" .-> NEXT
```

---

## Phase 2 — ECS task boot

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours  fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db    fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef infra fill:#ede9fe,stroke:#7c3aed,color:#2e1065;

    C4["ECS pulls image<br/>ECR interview-bot:latest"]:::infra
    C5["inject 8 secrets<br/>(Secrets Manager → env)"]:::infra
    C6["start container<br/>python trigger.py"]:::infra
    T6["config.py<br/>GET /api/interview/&#123;id&#125;"]:::ours
    D6["RDS<br/>SELECT InterviewDetail<br/>(interview+user+rubric+zoom+assignment)"]:::db
    SEC["OPENAI · RECALL · ELEVENLABS<br/>ZOOM×3 · SMTP · NGROK"]:::infra
    NOTE["merge over interview_config.json<br/>(LLM / audio / question defaults)"]:::ours
    NEXT["→ Phase 3"]:::ours

    C4 --> C5 --> C6 --> T6
    C5 --> SEC
    T6 --> D6
    T6 --> NOTE
    D6 --> NEXT
```

---

## Phase 3 — Meeting setup & notification

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    T7["trigger.py<br/>request Zoom token"]:::ours
    Z7["Zoom<br/>S2S OAuth token"]:::ext
    Z8["Zoom<br/>create meeting"]:::ext
    T9["trigger.py<br/>POST /api/zoom +<br/>PUT interview=STARTING<br/>(also prints join link to logs)"]:::ours
    D9["RDS<br/>INSERT zoom (stores join link)<br/>UPDATE interview"]:::db
    M10["Gmail SMTP<br/>email join link (optional)"]:::ext
    NEXT["→ Phase 4"]:::ours

    T7 --> Z7 --> Z8 --> T9
    T9 --> D9
    T9 -. optional .-> M10
    D9 --> NEXT
```

> The join link is **always** written to the DB (`POST /api/zoom`) so the student
> dashboard can show it, and it is printed to the bot's logs. The SMTP email is an
> optional convenience (mostly for headless runs) — a valid student email is not required.

---

## Phase 4 — Session init  (PARALLEL)

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;
    classDef gate fill:#fef9c3,stroke:#ca8a04,color:#422006;

    S11["PUT interview=RUNNING"]:::ours
    S12["start audio_ws :8766"]:::ours
    S13["open ngrok tunnel"]:::ours
    N13["ngrok<br/>public wss:// URL"]:::ext
    S14["recall create_bot<br/>join Zoom · audio_separate_raw→wss"]:::ours
    FORK{{"fork"}}:::gate

    TA["Track A — recall.ai<br/>poll until in_call_recording"]:::ext
    TB1["Track B — OpenAI<br/>gpt-4o-mini: X questions"]:::ext
    TB2["Track B — ElevenLabs<br/>TTS prefetch (Qs + closings)"]:::ext

    JOIN{{"join (both done)"}}:::gate
    NEXT["→ Phase 5"]:::ours

    S11 --> S12 --> S13 --> N13 --> S14 --> FORK
    FORK --> TA --> JOIN
    FORK --> TB1 --> TB2 --> JOIN
    JOIN --> NEXT
```

---

## Phase 5 — Student joins · intro

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    Z16["Zoom<br/>student joins"]:::ext
    S17["INTRO greeting<br/>(cached TTS)"]:::ours
    R17["recall.ai<br/>output_audio (play)"]:::ext
    S18{"heard<br/>'ready'?"}:::ours
    S19["start interview clock"]:::ours
    NEXT["→ Phase 6"]:::ours

    Z16 --> S17 --> R17 --> S18
    S18 -. "no — repeat" .-> S17
    S18 -- yes --> S19 --> NEXT
```

---

## Phase 6 — Question loop  ×5  ·  follow-up loop ×2

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    S20["ASK q[i]"]:::ours
    R20["recall.ai<br/>play question"]:::ext
    R21["recall.ai<br/>stream raw PCM"]:::ext
    N21["ngrok<br/>relay PCM"]:::ext
    W21["LISTEN<br/>queue → VAD → Whisper"]:::ours
    S22["append Q/A to transcript"]:::ours
    Q23{"more follow-ups?<br/>(max Y)"}:::ours
    O23["OpenAI<br/>gpt-4o-mini follow-up"]:::ext
    E23["ElevenLabs TTS"]:::ext
    R23["recall.ai play"]:::ext
    Q24{"more of<br/>the X Qs?"}:::ours
    NEXT["→ Phase 7"]:::ours

    S20 --> R20 --> R21 --> N21 --> W21 --> S22 --> Q23
    Q23 -- "yes *Y" --> O23 --> E23 --> R23 -. "back to LISTEN" .-> R21
    Q23 -- no --> Q24
    Q24 -. "yes → next line of questioning (*X)" .-> S20
    Q24 -- no --> NEXT
```

---

## Phase 7 — Wrap-up

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    T25{"time<br/>up?"}:::ours
    OPEN["OPEN_FLOOR prompt"]:::ours
    LIS["LISTEN once<br/>(recall → Whisper)"]:::ours
    CC["CLOSE_COMPLETE script"]:::ours
    CL["CLOSE script (time-up)"]:::ours
    R26["recall.ai<br/>play closing"]:::ext
    NEXT["→ Phase 8"]:::ours

    T25 -- no --> OPEN --> LIS --> CC --> R26
    T25 -- yes --> CL --> R26
    R26 --> NEXT
```

---

## Phase 8 — End procedure  (PARALLEL teardown)

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;
    classDef gate fill:#fef9c3,stroke:#ca8a04,color:#422006;

    S27["session finishing"]:::ours
    FORK{{"fan-out"}}:::gate
    A27["PUT interview=COMPLETED<br/>+ transcript"]:::ours
    D27["RDS<br/>UPDATE interview"]:::db
    R27["recall.ai<br/>leave_call"]:::ext
    Z28["Zoom<br/>end_meeting"]:::ext
    NEXT["→ Phase 9"]:::ours

    S27 --> FORK
    FORK --> A27 --> D27 --> NEXT
    FORK --> R27 --> NEXT
    FORK --> Z28 --> NEXT
```

---

## Phase 9 — Marking

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 28, "nodeSpacing": 22, "padding": 12, "htmlLabels": false}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;

    MK["marker.py<br/>GET interview + rubric"]:::ours
    D30["RDS<br/>SELECT interview, rubric"]:::db
    O31["OpenAI<br/>gpt-4o structured grading"]:::ext
    MP["POST /api/result"]:::ours
    D32["RDS<br/>INSERT result"]:::db
    FE33["Frontend /report/&#123;id&#125;<br/>GET interview + result"]:::ours

    MK --> O31 --> MP --> FE33
    MK --> D30
    MP --> D32
```

> Note — as in `../ARCHITECTURE.md`: in the live ECS path **Phase 9 (marking) is not
> auto-invoked** by `session.py` — it runs in the local CLI flow or must be
> triggered separately. The chart shows the intended complete flow.

---

To export per-slide images, render the whole file at high resolution with a transparent
background:

```
npx -p @mermaid-js/mermaid-cli mmdc -i INTERVIEW_BOT_FLOWCHART.md -o phase.png -w 2000 -s 4 -b transparent
```

This produces `phase-1.png` … `phase-10.png` (overview rail + nine phases), one per diagram.
