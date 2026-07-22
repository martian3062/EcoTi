"""Scam-Call Detection swarm.

Sub-agents: transcriber (faster-whisper) · script_matcher (pgvector embeddings) ·
voice_spoof (ASVspoof-trained) · verdict_writer.

EDGE mode runs transcription + first-pass scoring locally (Gemma via Ollama) so
it works with no network; cloud mode does full fusion. P0 returns deterministic
realistic outputs through the ``core.llm`` stub.
"""
from __future__ import annotations

import logging
import os
import tempfile

import requests
from core import llm
from core.events import A2AEvent, Module
from core.script_bank import match_script
from core.swarm import BaseSwarm, SubAgent

logger = logging.getLogger("ecoti.scam_call")


def _download_audio(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        suffix = os.path.splitext(url.split("?")[0])[1] or ".wav"
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        return path
    except Exception as exc:  # pragma: no cover - network optional
        logger.warning("audio download failed: %s", exc)
        return None


def _transcriber(state: dict) -> dict:
    """Real ASR (Groq Whisper / Sarvam Saarika) when an audio_url is given;
    otherwise a provided transcript or a deterministic stub."""
    edge = state.get("edge", False)
    transcript = state.get("transcript")
    asr_source = "provided" if transcript else "stub"
    audio_path = None
    if state.get("audio_url"):
        audio_path = _download_audio(state["audio_url"])  # kept for anti-spoof; cleaned in run()
        if audio_path and not transcript:
            transcript = llm.transcribe(audio_path, force_edge=edge, language=state.get("language"))
            asr_source = "asr"
    if not transcript:
        transcript = llm.transcribe(state.get("audio_ref", ""), force_edge=edge)
    return {
        "transcript": transcript,
        "asr_source": asr_source,
        "audio_path": audio_path,
        "edge_runtime": llm.runtime_info(force_edge=edge),
    }


def _script_matcher(state: dict) -> dict:
    match = match_script(state.get("transcript") or "")
    return {
        "script_match_score": match["score"],
        "matched_pattern": match["pattern_id"],
        "matched_script": match,
        "matched_markers": match["matched_markers"],
    }


def _voice_spoof(state: dict) -> dict:
    # Real pretrained wav2vec2 deepfake detector (zero training) when a real
    # audio file is present; otherwise deterministic stub for the demo refs.
    if state.get("audio_path") and not state.get("edge"):
        real = llm.classify_audio_spoof(state["audio_path"])
        if real is not None:
            return {
                "voice_spoof_score": real["score"],
                "synthetic_voice": real["synthetic"],
                "voice_indicators": [f"wav2vec2:{real['label']}"],
                "voice_model": real["model"],
            }
    ref = state.get("audio_ref", "")
    synthetic = "scam" in ref or state.get("script_match_score", 0) >= 0.6
    indicators = []
    if "scam" in ref:
        indicators.append("known_synthetic_demo_ref")
    if state.get("script_match_score", 0) >= 0.6:
        indicators.append("coerced_script_tone")
    return {
        "voice_spoof_score": 0.91 if synthetic else 0.07,
        "synthetic_voice": synthetic,
        "voice_indicators": indicators,
    }


def _verdict_writer(state: dict) -> dict:
    s = max(state.get("script_match_score", 0), state.get("voice_spoof_score", 0) * 0.9)
    verdict = "scam" if s >= 0.6 else "suspicious" if s >= 0.3 else "safe"
    out = {"verdict": verdict, "confidence": round(s, 2)}
    # Real GenAI rationale via the cloud reasoning tier (Groq/Kimi). The numeric
    # verdict stays deterministic (keeps fusion thresholds stable); the LLM only
    # explains it. Skipped on the edge path and when no key is configured.
    if verdict != "safe" and not state.get("edge"):
        rationale = llm.complete(
            f"A caller said: \"{(state.get('transcript') or '')[:400]}\". In one or two "
            f"sentences explain to the victim why this is a '{verdict}' fraud attempt and "
            f"the single most important action to take.",
            system="You are EcoTi's scam-call analyst. Be brief, protective, and cite the 1930 helpline.",
        )
        if rationale and not rationale.startswith("[stub-verdict]"):
            out["rationale"] = rationale.strip()
    return out


swarm = BaseSwarm(
    name="scam_call",
    sub_agents=[
        SubAgent("transcriber", _transcriber),
        SubAgent("script_matcher", _script_matcher),
        SubAgent("voice_spoof", _voice_spoof),
        SubAgent("verdict_writer", _verdict_writer),
    ],
)


def run(inputs: dict) -> dict:
    state = swarm.run(inputs)
    # clean up any downloaded audio temp file
    if state.get("audio_path"):
        try:
            os.remove(state["audio_path"])
        except OSError:
            pass
    state["event"] = A2AEvent(
        module=Module.SCAM_CALL.value,
        signal="scam_call_verdict",
        identifier=inputs.get("identifier"),
        confidence=state.get("confidence", 0.0),
        route="edge" if inputs.get("edge") else "cloud",
        payload={
            "verdict": state.get("verdict"),
            "matched_pattern": state.get("matched_pattern"),
            "matched_script": state.get("matched_script"),
            "synthetic_voice": state.get("synthetic_voice"),
            "voice_indicators": state.get("voice_indicators"),
            "voice_model": state.get("voice_model"),
            "rationale": state.get("rationale"),
            "asr_source": state.get("asr_source"),
            "edge_runtime": state.get("edge_runtime"),
            "sub_confidences": {
                "script_match": state.get("script_match_score"),
                "voice_spoof": state.get("voice_spoof_score"),
            },
            "transcript": state.get("transcript"),
        },
    )
    return state
