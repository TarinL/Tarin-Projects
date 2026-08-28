# Interview Bot — Client Setup Guide

## Prerequisites

Install **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** and make sure it is running before proceeding.
That is the only software you need to install.

---

## First-time setup

### 1. Add your API keys

A file called `.env` is included with the keys already filled in.
You should not need to change anything here unless you want to use your own accounts.

### 2. Edit the interview configuration

Open `interview_config.json` in any text editor. This file controls everything about the interview:

| Section | What to change |
|---|---|
| `student` | Name and ID of the student being interviewed |
| `assignment` | Topic, assignment name, and marking rubric |
| `interview` | Duration, formality level, number of follow-up questions |
| `questions` | The questions the bot will ask, and their relative weights |
| `audio` | ElevenLabs voice ID and model, Whisper STT settings |
| `scheduling` | Student email (for the Zoom invite), scheduled start time |

Lines starting with `"_comment"` are notes — they are ignored by the bot and safe to leave in.

### 3. Build and run

Open a terminal, navigate to this folder, and run:

```
docker compose up --build
```

The first run will take a few minutes — Docker is downloading the Whisper speech-to-text model (~150 MB). Subsequent runs start in seconds.

The bot will create a Zoom meeting, email the join link to the student, wait until the scheduled start time, then join and conduct the interview automatically.

---

## Running immediately (skipping the countdown)

The default configuration launches the bot straight away, ignoring the `scheduled_start` time in the config. This is useful for testing.

To have the bot wait until the scheduled time instead, open `docker-compose.yml` and remove `--now` from the `command` line.

---

## Changing the configuration between runs

Edit `interview_config.json` and re-run `docker compose up`. You do **not** need to rebuild the image (`--build`) after the first run unless you are told to.

---

## Stopping the bot

Press `Ctrl+C` in the terminal window where Docker is running.

---

## Troubleshooting

**The bot does not speak / student cannot hear anything**
Check that `ELEVENLABS_API_KEY` in `.env` is correct.

**Zoom meeting is not created**
Check the `ZOOM_ACCOUNT_ID`, `ZOOM_CLIENT_ID`, and `ZOOM_CLIENT_SECRET` values in `.env`.

**"ngrok" errors on startup**
Check that `NGROK_AUTH_TOKEN` in `.env` is correct. Each ngrok account can only run one tunnel at a time — make sure no other instance of the bot is running.
