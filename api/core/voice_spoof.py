"""Local voice anti-spoof — real pretrained wav2vec2 deepfake detector.

HF's free serverless doesn't host audio-deepfake models, so we import the
weights and run inference locally via transformers (CPU). Model:
``MelodyMachine/Deepfake-audio-detection-V2`` (Wav2Vec2ForSequenceClassification,
labels {0: fake, 1: real}). Lazy singleton; any failure returns None so the
scam-call swarm falls back to its deterministic detector.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger("ecoti.voice")

_pipe = None
_tried = False


def _pipeline():
    global _pipe, _tried
    if _tried:
        return _pipe
    _tried = True
    try:
        from transformers import pipeline

        _pipe = pipeline("audio-classification", model=settings.VOICE_MODEL)
        logger.info("voice anti-spoof model loaded: %s", settings.VOICE_MODEL)
    except Exception as exc:  # pragma: no cover - heavy/optional
        logger.warning("voice model unavailable: %s", exc)
        _pipe = None
    return _pipe


def classify(path: str) -> dict | None:
    """Return {synthetic, score, label, model} for an audio file, or None."""
    pipe = _pipeline()
    if pipe is None or not path:
        return None
    try:
        preds = pipe(path, top_k=None)  # ffmpeg decodes the file
        if not preds:
            return None
        top = max(preds, key=lambda p: p.get("score", 0))
        label = str(top.get("label", "")).lower()
        synthetic = any(k in label for k in ("fake", "spoof", "synthetic", "deepfake", "generated"))
        # score = probability the voice is synthetic
        score = top["score"] if synthetic else round(1 - top["score"], 3)
        return {
            "synthetic": synthetic,
            "score": round(float(score), 3),
            "label": top.get("label"),
            "model": settings.VOICE_MODEL,
        }
    except Exception as exc:  # pragma: no cover
        logger.warning("voice classify failed: %s", exc)
        return None
