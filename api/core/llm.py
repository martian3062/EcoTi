"""LLM / AI provider router.

A single entry point used by every agent. Backends:
  * ``stub``   - deterministic canned outputs. No GPU, no network, no keys. (default)
  * ``ollama`` - local/edge models via the Ollama HTTP API (offline-capable).
  * ``groq``   - fast cloud (Llama/Kimi chat + Whisper ASR).
  * ``kimi``   - Moonshot Kimi long-context cloud reasoning (OpenAI-compatible).
  * ``sarvam`` - sovereign Indic AI: Saarika ASR, Mayura translate, Sarvam-M chat.

Agents call :func:`complete`, :func:`transcribe`, :func:`translate`, :func:`embed`,
:func:`vision`. Every backend degrades to the deterministic stub on any error, so
the demo never goes dark (self-healing at the model tier).
"""
from __future__ import annotations

import hashlib
import logging
import os

import requests
from django.conf import settings

logger = logging.getLogger("ecoti.llm")

_TIMEOUT = 30


def provider() -> str:
    return getattr(settings, "LLM_PROVIDER", "stub")


def runtime_info(*, force_edge: bool = False) -> dict:
    """Expose the selected runtime without making a network call."""
    selected = provider()
    if force_edge and selected in {"groq", "kimi", "sarvam"}:
        selected = "ollama"
    return {
        "provider": selected,
        "requested_edge": force_edge,
        "offline_ready": selected in {"stub", "ollama"},
        "ollama_base_url": getattr(settings, "OLLAMA_BASE_URL", ""),
        "ollama_model": getattr(settings, "OLLAMA_MODEL", ""),
        "groq_model": getattr(settings, "GROQ_MODEL", ""),
        "kimi_model": getattr(settings, "KIMI_MODEL", ""),
        "sarvam_model": getattr(settings, "SARVAM_CHAT_MODEL", ""),
    }


def _stub_hash_float(text: str) -> float:
    h = hashlib.sha256(text.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


# ----------------------------------------------------------------------- complete
def complete(prompt: str, system: str = "", *, force_edge: bool = False) -> str:
    """Chat/reasoning. Honours force_edge (citizen/field tools prefer on-device)."""
    p = provider()
    if force_edge and p in {"groq", "kimi", "sarvam"}:
        p = "ollama"

    order = {
        "groq": [_groq_complete],
        "kimi": [_kimi_complete, _groq_complete],
        "sarvam": [_sarvam_complete, _groq_complete],
        "ollama": [_ollama_complete],
    }.get(p, [])

    for fn in order:
        try:
            out = fn(prompt, system)
            if out:
                return out
        except Exception as exc:  # pragma: no cover - network optional
            logger.warning("%s failed: %s", fn.__name__, exc)

    return _stub_complete(prompt, system)


def _stub_complete(prompt: str, system: str) -> str:
    return f"[stub-verdict] {prompt[:120]}"


def _openai_chat(base_url: str, key: str, model: str, prompt: str, system: str,
                 auth_header: str = "Authorization", auth_prefix: str = "Bearer ") -> str:
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={auth_header: f"{auth_prefix}{key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system or "You are a fraud-intelligence analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _groq_complete(prompt: str, system: str) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("no GROQ_API_KEY")
    return _openai_chat("https://api.groq.com/openai/v1", settings.GROQ_API_KEY,
                        settings.GROQ_MODEL, prompt, system)


def _kimi_complete(prompt: str, system: str) -> str:
    if not settings.KIMI_API_KEY:
        raise RuntimeError("no KIMI_API_KEY")
    return _openai_chat(settings.KIMI_BASE_URL, settings.KIMI_API_KEY,
                        settings.KIMI_MODEL, prompt, system)


def _sarvam_complete(prompt: str, system: str) -> str:
    if not settings.SARVAM_API_KEY:
        raise RuntimeError("no SARVAM_API_KEY")
    # Sarvam chat is OpenAI-compatible but authenticates via api-subscription-key.
    return _openai_chat(f"{settings.SARVAM_BASE_URL}/v1", settings.SARVAM_API_KEY,
                        settings.SARVAM_CHAT_MODEL, prompt, system,
                        auth_header="api-subscription-key", auth_prefix="")


def _ollama_complete(prompt: str, system: str) -> str:
    resp = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "system": system, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


# --------------------------------------------------------------------- transcribe
def transcribe(audio_ref: str, *, force_edge: bool = False, language: str | None = None) -> str:
    """Speech-to-text. Uses a real ASR API when ``audio_ref`` is an existing file
    and a provider is configured; otherwise returns a deterministic stub transcript
    (keeps the demo working with no audio / no network)."""
    is_file = bool(audio_ref) and os.path.isfile(audio_ref)
    p = provider()
    if is_file and not force_edge:
        try:
            if p == "sarvam" and settings.SARVAM_API_KEY:
                return _sarvam_asr(audio_ref, language)
            if settings.GROQ_API_KEY:
                return _groq_whisper(audio_ref, language)
        except Exception as exc:  # pragma: no cover
            logger.warning("ASR failed, using stub transcript: %s", exc)
    return _STUB_TRANSCRIPTS.get(audio_ref, _DEFAULT_SCAM_TRANSCRIPT)


def _groq_whisper(path: str, language: str | None) -> str:
    with open(path, "rb") as f:
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            files={"file": f},
            data={"model": settings.GROQ_WHISPER_MODEL, **({"language": language} if language else {})},
            timeout=90,
        )
    resp.raise_for_status()
    return resp.json().get("text", "")


def _sarvam_asr(path: str, language: str | None) -> str:
    with open(path, "rb") as f:
        resp = requests.post(
            f"{settings.SARVAM_BASE_URL}/speech-to-text",
            headers={"api-subscription-key": settings.SARVAM_API_KEY},
            files={"file": f},
            data={"model": "saarika:v2", **({"language_code": language} if language else {})},
            timeout=90,
        )
    resp.raise_for_status()
    return resp.json().get("transcript", "")


# ---------------------------------------------------------------------- translate
def translate(text: str, target_lang: str, source_lang: str = "en-IN") -> str:
    """Indic translation via Sarvam Mayura; stub returns the input unchanged.
    Runs whenever a Sarvam key is present, independent of the chat provider."""
    if settings.SARVAM_API_KEY and target_lang not in {"en", "en-IN"}:
        try:
            resp = requests.post(
                f"{settings.SARVAM_BASE_URL}/translate",
                headers={"api-subscription-key": settings.SARVAM_API_KEY},
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": _sarvam_lang(target_lang),
                    "model": "mayura:v1",
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get("translated_text", text)
        except Exception as exc:  # pragma: no cover
            logger.warning("Sarvam translate failed: %s", exc)
    return text


# -------------------------------------------------------- text-to-speech (anchor)
def tts(text: str, lang: str = "en", speaker: str = "anushka") -> str | None:
    """Human-sounding TTS via Sarvam Bulbul (India-accented, multilingual).
    Returns base64 WAV, or None if unavailable (frontend falls back to browser TTS)."""
    if not settings.SARVAM_API_KEY or not text:
        return None
    try:
        resp = requests.post(
            f"{settings.SARVAM_BASE_URL}/text-to-speech",
            headers={"api-subscription-key": settings.SARVAM_API_KEY},
            json={
                "inputs": [text[:480]],
                "target_language_code": _sarvam_lang(lang),
                "speaker": speaker,
                "model": "bulbul:v2",
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        audios = resp.json().get("audios", [])
        return audios[0] if audios else None
    except Exception as exc:  # pragma: no cover
        logger.warning("Sarvam TTS failed: %s", exc)
        return None


# ------------------------------------------------------- audio anti-spoof (voice)
def classify_audio_spoof(path: str) -> dict | None:
    """Real AI-voice / deepfake detection via a locally-imported pretrained
    wav2vec2 model (zero training). Returns {synthetic, score, label} or None."""
    from . import voice_spoof

    return voice_spoof.classify(path)


# ------------------------------------------------------------ counterfeit VLM
def vision_note_check(image_bytes: bytes, denomination: str = "500") -> dict | None:
    """Zero-shot counterfeit note check via the Kimi (Moonshot) vision model.
    Returns {raw, model} or None when unavailable."""
    if not settings.KIMI_API_KEY or not image_bytes:
        return None
    import base64

    b64 = base64.b64encode(image_bytes).decode()
    prompt = (
        f"You are a currency authentication expert. Examine this Indian Rs.{denomination} banknote. "
        "Check security features: watermark, security thread, microprint, intaglio print, serial-number "
        "font. Respond ONLY as JSON: {\"verdict\":\"genuine|counterfeit|uncertain\", "
        "\"rationale\":\"...\", \"failing_features\":[...]}."
    )
    model = getattr(settings, "KIMI_VISION_MODEL", "moonshot-v1-8k-vision-preview")
    try:
        resp = requests.post(
            f"{settings.KIMI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.KIMI_API_KEY}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
                "max_tokens": 400,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return {"raw": content, "model": model}
    except Exception as exc:  # pragma: no cover
        logger.warning("Kimi VLM note check failed: %s", exc)
        return None


def _sarvam_lang(code: str) -> str:
    """Map short lang codes to Sarvam BCP-47 codes."""
    return {
        "hi": "hi-IN", "ta": "ta-IN", "kn": "kn-IN", "te": "te-IN", "ml": "ml-IN",
        "mr": "mr-IN", "gu": "gu-IN", "bn": "bn-IN", "pa": "pa-IN", "or": "od-IN",
        "as": "as-IN", "en": "en-IN",
    }.get(code, code)


# ------------------------------------------------------------------------- embed
def embed(text: str) -> list[float]:
    """Embedding vector. HF Inference (MuRIL) when configured, else deterministic stub."""
    if settings.HF_TOKEN:
        try:
            # HF migrated inference to the router; feature-extraction pipeline.
            resp = requests.post(
                f"https://router.huggingface.co/hf-inference/models/{settings.HF_EMBED_MODEL}/pipeline/feature-extraction",
                headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
                json={"inputs": text},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            # feature-extraction may return token-level vectors -> mean-pool
            if isinstance(data, list) and data and isinstance(data[0], list):
                cols = list(zip(*data)) if isinstance(data[0][0], (int, float)) else None
                if cols:
                    return [sum(c) / len(c) for c in cols]
            if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
                return data
        except Exception as exc:  # pragma: no cover
            logger.warning("HF embed failed, using stub: %s", exc)
    if provider() == "ollama":
        try:
            resp = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": settings.OLLAMA_MODEL, "prompt": text},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as exc:  # pragma: no cover
            logger.warning("Ollama embed failed, using stub: %s", exc)
    h = hashlib.sha256(text.encode()).digest()
    return [b / 255.0 for b in h[:16]]


# ------------------------------------------------------------------------- vision
def vision(image_ref: str, prompt: str = "") -> dict:
    """VLM hook for counterfeit note check. Stub returns deterministic scores."""
    seed = _stub_hash_float(image_ref)
    return {"raw": f"[stub-vision:{image_ref}]", "seed": seed}


def health() -> dict:
    """Which real providers are reachable right now (for the dashboard/demo)."""
    out = {"provider": provider()}
    checks = {
        "groq": (bool(settings.GROQ_API_KEY), "https://api.groq.com/openai/v1/models",
                 {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}),
        "kimi": (bool(settings.KIMI_API_KEY), f"{settings.KIMI_BASE_URL}/models",
                 {"Authorization": f"Bearer {settings.KIMI_API_KEY}"}),
        "sarvam": (bool(settings.SARVAM_API_KEY), f"{settings.SARVAM_BASE_URL}/v1/models",
                   {"api-subscription-key": settings.SARVAM_API_KEY}),
        "huggingface": (bool(settings.HF_TOKEN), "https://huggingface.co/api/whoami-v2",
                        {"Authorization": f"Bearer {settings.HF_TOKEN}"}),
        "firecrawl": (bool(settings.FIRECRAWL_API_KEY), None, None),
    }
    for name, (configured, url, headers) in checks.items():
        if not configured:
            out[name] = "not_configured"
            continue
        if url is None:
            out[name] = "configured"
            continue
        try:
            r = requests.get(url, headers=headers, timeout=8)
            out[name] = "ok" if r.status_code < 400 else f"http_{r.status_code}"
        except Exception:
            out[name] = "unreachable"
    return out


_DEFAULT_SCAM_TRANSCRIPT = (
    "Sir this is CBI. A case is registered against your Aadhaar. "
    "Do not disconnect, this is a digital arrest. Transfer the amount to clear your name."
)
_STUB_TRANSCRIPTS = {
    "demo_scam_call.wav": (
        "Sir this is CBI officer Sharma. Your Aadhaar is linked to a money laundering "
        "case. This is a digital arrest. Stay on video call. Do not tell anyone. "
        "To verify you are innocent, transfer the funds to this RBI account now."
    ),
    "demo_safe_call.wav": "Hi, this is your bank reminding you about your card statement due date.",
}
