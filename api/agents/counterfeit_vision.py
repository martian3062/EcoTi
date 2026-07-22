"""Counterfeit Currency Vision swarm.

Sub-agents: feature_locator · microprint_checker · serial_validator ·
authenticity_scorer. P1 uses a PyTorch tile-MIL classifier + feature-localisation
head and an on-device VLM (Qwen-VL) so images never leave the teller's phone.
P0 returns deterministic per-feature scores + a heatmap/box overlay payload.
"""
from __future__ import annotations

import base64
import json
import logging
import re

import requests

from core import llm
from core.events import A2AEvent, Module
from core.swarm import BaseSwarm, SubAgent

logger = logging.getLogger("ecoti.counterfeit")

_FEATURES = ["microprint", "security_thread", "watermark", "intaglio", "serial_font"]


def _image_bytes(inputs: dict) -> bytes | None:
    if inputs.get("image_b64"):
        try:
            return base64.b64decode(inputs["image_b64"].split(",")[-1])
        except Exception:
            return None
    if inputs.get("image_url"):
        try:
            r = requests.get(inputs["image_url"], timeout=20)
            r.raise_for_status()
            return r.content
        except Exception as exc:  # pragma: no cover
            logger.warning("note image download failed: %s", exc)
    return None


def _vlm_check(inputs: dict) -> dict | None:
    """Zero-shot VLM authenticity check (real, no training) when an image is given."""
    img = _image_bytes(inputs)
    if img is None:
        return None
    out = llm.vision_note_check(img, inputs.get("denomination", "500"))
    if not out:
        return None
    raw = out.get("raw", "")
    parsed = {}
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            parsed = json.loads(m.group(0))
        except Exception:
            parsed = {}
    verdict = (parsed.get("verdict") or "").lower()
    if verdict not in {"genuine", "counterfeit", "uncertain"}:
        verdict = "counterfeit" if "counterfeit" in raw.lower() else "genuine" if "genuine" in raw.lower() else "uncertain"
    return {
        "verdict": verdict,
        "rationale": parsed.get("rationale") or raw[:300],
        "failing_features": parsed.get("failing_features", []),
        "model": out.get("model"),
    }


def _feature_locator(state: dict) -> dict:
    seed = llm.vision(state.get("image_ref", ""), "locate security features")["seed"]
    # Deterministic per-feature scores; a "fake" image ref pushes them down.
    fake = "fake" in state.get("image_ref", "").lower()
    scores = {}
    for i, f in enumerate(_FEATURES):
        base = (seed * 1000 % (i + 7)) / (i + 7)
        scores[f] = round(max(0.05, base * (0.4 if fake else 1.0)), 2)
    return {"feature_scores": scores}


def _microprint_checker(state: dict) -> dict:
    s = state["feature_scores"]["microprint"]
    return {"microprint_ok": s >= 0.5}


def _serial_validator(state: dict) -> dict:
    s = state["feature_scores"]["serial_font"]
    return {"serial_ok": s >= 0.5}


def _authenticity_scorer(state: dict) -> dict:
    scores = state["feature_scores"]
    avg = sum(scores.values()) / len(scores)
    failing = [f for f, v in scores.items() if v < 0.5]
    verdict = "counterfeit" if failing else "genuine"
    return {
        "verdict": verdict,
        "confidence": round(1 - avg if verdict == "counterfeit" else avg, 2),
        "failing_features": failing,
        "overlay": {"boxes": [{"feature": f, "score": scores[f]} for f in failing]},
    }


swarm = BaseSwarm(
    name="counterfeit_vision",
    sub_agents=[
        SubAgent("feature_locator", _feature_locator),
        SubAgent("microprint_checker", _microprint_checker),
        SubAgent("serial_validator", _serial_validator),
        SubAgent("authenticity_scorer", _authenticity_scorer),
    ],
)


def run(inputs: dict) -> dict:
    state = swarm.run(inputs)
    # Real zero-shot VLM overrides the deterministic verdict when an image is given.
    vlm = _vlm_check(inputs)
    method = "tile_mil_stub"
    if vlm is not None:
        state["verdict"] = vlm["verdict"]
        state["vlm_rationale"] = vlm["rationale"]
        if vlm["failing_features"]:
            state["failing_features"] = vlm["failing_features"]
        method = f"vlm:{vlm.get('model')}"
    state["event"] = A2AEvent(
        module=Module.COUNTERFEIT_VISION.value,
        signal="counterfeit_verdict",
        identifier=inputs.get("identifier"),
        confidence=state.get("confidence", 0.0),
        route="edge",
        payload={
            "verdict": state.get("verdict"),
            "denomination": inputs.get("denomination", "500"),
            "feature_scores": state.get("feature_scores"),
            "failing_features": state.get("failing_features"),
            "vlm_rationale": state.get("vlm_rationale"),
            "method": method,
            "overlay": state.get("overlay"),
        },
    )
    return state
