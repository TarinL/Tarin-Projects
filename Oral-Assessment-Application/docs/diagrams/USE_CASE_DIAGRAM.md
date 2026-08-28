# UML use case diagram

Who does what with VivāVoce. Mermaid has no native use-case diagram type, so this uses the
standard convention: actors as side nodes, use cases as ovals (stadium nodes) inside the system
boundary, `---` for association, dashed arrows for `«include»`. The narrative version of each
flow is in [../ARCHITECTURE.md](../ARCHITECTURE.md).

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial"}, "flowchart": {"defaultRenderer": "elk", "rankSpacing": 45, "nodeSpacing": 32, "padding": 14}}}%%
flowchart LR
    classDef actor fill:#fef3c7,stroke:#d97706,color:#431407;
    classDef uc fill:#dbeafe,stroke:#2563eb,color:#0b2447;
    classDef sys fill:none,stroke:#94a3b8,color:#334155;

    INSTR(["👤 Instructor"]):::actor
    STUD(["👤 Student"]):::actor
    BOT(["🤖 Interview bot<br/>(system actor)"]):::actor

    subgraph SYSTEM["VivāVoce"]
        direction TB
        UC_AUTH([Sign in<br/>via Cognito]):::uc
        UC_CLASS([Manage classes &<br/>enrol students]):::uc
        UC_CREATE([Create assignment<br/>Standard / Review / Knowledge]):::uc
        UC_SCHED([Schedule interview<br/>duration & due date]):::uc
        UC_REVIEW([Review suggested grade<br/>& marking report]):::uc
        UC_VIEW([View upcoming &<br/>completed interviews]):::uc
        UC_START([Trigger scheduled<br/>interview]):::uc
        UC_JOIN([Join Zoom call<br/>via dashboard link]):::uc
        UC_FACE([Watch live bot-face<br/>visualiser]):::uc
        UC_CONDUCT([Conduct oral interview<br/>questions & follow-ups]):::uc
        UC_MARK([Mark transcript<br/>against rubric]):::uc
        UC_LINK([Publish join link<br/>dashboard + optional email]):::uc
    end
    class SYSTEM sys

    INSTR --- UC_AUTH
    INSTR --- UC_CLASS
    INSTR --- UC_CREATE
    INSTR --- UC_SCHED
    INSTR --- UC_REVIEW

    STUD --- UC_AUTH
    STUD --- UC_VIEW
    STUD --- UC_START
    STUD --- UC_JOIN
    STUD --- UC_FACE

    UC_START -.->|"include"| UC_LINK
    UC_JOIN -.->|"include"| UC_CONDUCT
    UC_CONDUCT -.->|"include"| UC_MARK
    UC_MARK -.-> UC_REVIEW

    BOT --- UC_LINK
    BOT --- UC_CONDUCT
    BOT --- UC_MARK
```

- The **interview bot** is modelled as a secondary (system) actor: it is launched by the system
  when a student triggers an interview, then drives the Zoom call, marking, and join-link
  publication itself.
- `Sign in` is shared: both roles authenticate against the same Cognito pool; the group
  (Teachers/Students) selects the dashboard.
- The join link always reaches the student dashboard; emailing it is optional.

> **Export:** rendered PNG committed alongside (`use_case_diagram-1.png`). Regenerate with:
> `npx -p @mermaid-js/mermaid-cli mmdc -i USE_CASE_DIAGRAM.md -o use_case_diagram.png -w 2000 -s 4 -b transparent`
