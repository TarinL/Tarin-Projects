# Scripts

Developer utilities for preparing and seeding interviews. Run them from the bot root, e.g.
`python scripts/seed_interview.py`.

- `apply_to_config.py` — populate `interview_config.json` from an external submission
  (`--submission file.txt`) or a generated KB assessment (`--kb-assessment file.json`).
- `seed_interview.py` — create a test interview in the database from `interview_config.json`.
