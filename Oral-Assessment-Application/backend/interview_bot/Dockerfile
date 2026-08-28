FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by faster-whisper / av / sounddevice build chain.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the Whisper STT model so it's available immediately at runtime.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu', compute_type='int8')"

# Pre-download the ngrok binary so it's available immediately at runtime.
RUN python -c "from pyngrok import ngrok; ngrok.install_ngrok()"

# In ECS, pass secrets and INTERVIEW_ID as environment variable overrides.
# All API keys (OPENAI_API_KEY, RECALL_API_KEY, ELEVENLABS_API_KEY, ZOOM_*, DB_API_KEY)
# should be injected via ECS Task Definition secrets (AWS Secrets Manager).
#
# Typical ECS invocation:
#   Environment overrides: INTERVIEW_ID=<id>
#   The trigger reads the Zoom join URL from the DB record and skips meeting creation.

ENTRYPOINT ["python", "zoom_integration/trigger.py"]

# Default: start immediately (no countdown wait). The scheduled_start from the DB
# is used for logging only when --now is passed. Remove --now for time-gated execution.
CMD ["--now"]
