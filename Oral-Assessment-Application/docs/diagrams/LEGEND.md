# Diagram Legend

Shared key for `INTERVIEW_BOT_FLOWCHART.md` and `SYSTEM_MAP.md`.

> Note: this file intentionally keeps HTML labels **on** (no `htmlLabels:false`) so the
> coloured-square emoji render in colour. If you export it to PNG and the boxes clip,
> raise `padding` in the init line.

---

## Box colours — what each section is

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"padding": 12, "nodeSpacing": 25, "rankSpacing": 35}}}%%
flowchart LR
    classDef ours fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef db   fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef aws  fill:#ede9fe,stroke:#7c3aed,color:#2e1065;
    classDef ext  fill:#ffedd5,stroke:#ea580c,color:#431407;
    classDef gate fill:#fef9c3,stroke:#ca8a04,color:#422006;

    L1["🟦 Our code<br/>frontend · .NET API · Python bot"]:::ours
    L2["🟩 Our database<br/>RDS MySQL (always via the API)"]:::db
    L3["🟪 AWS managed infra<br/>ECS · ECR · Secrets · CloudWatch · CloudFront · Cognito · S3"]:::aws
    L4["🟧 External paid SaaS<br/>OpenAI · Zoom · recall.ai · ngrok · ElevenLabs · SMTP"]:::ext
    L5["Fork / join gate<br/>parallel split &amp; merge"]:::gate

    L1 ~~~ L2 ~~~ L3 ~~~ L4 ~~~ L5
```

---

## Arrows & connectors — what each line means

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"padding": 12, "nodeSpacing": 25, "rankSpacing": 35}}}%%
flowchart LR
    classDef plain fill:#ffffff,stroke:#94a3b8,color:#0f172a;
    classDef gate  fill:#fef9c3,stroke:#ca8a04,color:#422006;

    S1["A"]:::plain -->|"solid — live call / main flow"| S2["B"]:::plain
    S2 ~~~ D1["A"]:::plain
    D1 -. "dashed — async, loop-back, or auth / planned" .-> D2["B"]:::plain
    D2 ~~~ B1["A"]:::plain
    B1 <-->|"double — two-way link (e.g. recall.ai ↔ Zoom)"| B2["B"]:::plain
    B2 ~~~ F1{{"fork"}}:::gate
    F1 -->|"split into / merge from parallel branches"| F2{{"join"}}:::gate
```

---

### Export

```
npx -p @mermaid-js/mermaid-cli mmdc -i LEGEND.md -o legend.png -w 1600 -s 4 -b transparent
```

Produces `legend-1.png` (colours) and `legend-2.png` (arrows).
