# Database — entity relationship diagram

The `interviewDb` MySQL schema (RDS, MySQL 8.4). Canonical DDL:
`backend/InterviewApi/Data/sql/000_local_full_schema.sql` plus the numbered migrations in the
same folder. Full column notes are in [../components/database.md](../components/database.md).

> **Note:** the schema defines **no DDL foreign keys** — every relationship below is enforced in
> application code (the .NET API and the bot), matching the project convention. Cardinalities
> show intent, not constraints. `result.id == interview.id` once an interview is marked
> (migration 003), and rubrics are owned by the **assignment**, not the interview.
>
> Other column notes that don't fit the boxes: `user.student_id` is the UoA student ID (not
> auto-increment); `user.email` is optional (only smooths headless runs); `instructor.id` is the
> 9-digit ID entered at account creation; `zoom.meeting_id` is an INT too small for real Zoom
> meeting IDs, so the bot stores `0` (known bug); `result.grade` is a packed string like
> `Criterion: 8/10 | … || TOTAL: 42/50`.

```mermaid
%%{init: {"themeVariables": {"fontFamily": "arial", "fontSize": "18px"}, "er": {"layoutDirection": "TB", "minEntityWidth": 90, "entityPadding": 12, "fontSize": 18}}}%%
erDiagram
    instructor ||--o{ class_table : "owns"
    class_table ||--o{ class_student : "enrols"
    user ||--o{ class_student : "enrolled in"
    class_table ||--o{ assignment : "has"
    assignment ||--o| rubric : "owns"
    assignment ||--o{ interview : "assessed by"
    user ||--o{ interview : "sits"
    interview ||--o| zoom : "meeting"
    interview ||--o| result : "graded as"

    user {
        INT student_id PK "UoA student ID"
        VARCHAR username
        VARCHAR email "optional"
    }

    instructor {
        INT id PK "9-digit"
        VARCHAR name
    }

    class_table["class"] {
        INT id PK
        VARCHAR name
        INT instructor_id FK
    }

    class_student {
        INT class_id PK,FK
        INT student_id PK,FK
    }

    assignment {
        INT id PK
        VARCHAR name
        TEXT contents
        VARCHAR mode "manual|submission|knowledge_base"
        LONGTEXT knowledge_base
        LONGTEXT questions "JSON [{text, weight}]"
        INT class_id FK
        INT rubric_id FK "owns its rubric"
    }

    rubric {
        INT id PK
        LONGTEXT rubric_contents "JSON"
    }

    interview {
        INT id PK
        INT student_id FK
        INT zoom_id FK
        LONGTEXT transcript
        DATETIME start_time
        VARCHAR status "scheduled|ready|…"
        INT duration "minutes"
        DATETIME due_date
        TEXT additional_info
        INT assignment_id FK
        LONGTEXT student_submission
        INT result_id FK "= interview.id"
    }

    zoom {
        INT id PK
        VARCHAR url "join link"
        INT meeting_id "stored 0 (bug)"
    }

    result {
        INT id PK "= interview.id (1:1)"
        LONGTEXT transcript
        VARCHAR grade "packed string"
        LONGTEXT feedback
    }
```

> **Export:** rendered PNG committed alongside (`database_erd-1.png`). Regenerate with:
> `npx -p @mermaid-js/mermaid-cli mmdc -i DATABASE_ERD.md -o database_erd.png -w 2000 -s 4 -b transparent`
