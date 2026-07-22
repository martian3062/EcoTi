FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the voice anti-spoof model into the image so first inference is instant.
ARG VOICE_MODEL=MelodyMachine/Deepfake-audio-detection-V2
RUN python -c "from transformers import pipeline; pipeline('audio-classification', model='${VOICE_MODEL}')" || true

COPY . .

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "ecoti.asgi:application"]
