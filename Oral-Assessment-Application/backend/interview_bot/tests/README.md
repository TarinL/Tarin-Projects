# Bot tests

Headless / offline testing for the interview bot — no Zoom or audio hardware needed.

- `test_runner.py` — simulates a full interview against an LLM-driven "student"
  (`--profile strong|average|weak`) and writes a transcript. Run it from anywhere:

  ```bash
  python tests/test_runner.py --profile average
  ```

- `test_transcripts/` — sample and generated interview transcripts.
- `test_output.txt`, `test_output2.txt` — captured runs kept for reference.
