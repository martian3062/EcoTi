"""Digital-arrest and financial-fraud script bank.

P1 keeps this local and deterministic so the demo works without pgvector. The
same interface can later load embeddings from Postgres/pgvector.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from . import llm


@dataclass(frozen=True)
class ScriptPattern:
    id: str
    label: str
    severity: str
    markers: tuple[str, ...]
    templates: tuple[str, ...]


SCRIPT_PATTERNS: tuple[ScriptPattern, ...] = (
    ScriptPattern(
        id="digital_arrest_v1",
        label="Digital arrest impersonation",
        severity="critical",
        markers=(
            "digital arrest",
            "cbi",
            "police",
            "aadhaar",
            "money laundering",
            "do not disconnect",
            "stay on video",
            "do not tell anyone",
            "rbi account",
            "transfer",
            "clear your name",
        ),
        templates=(
            "This is CBI. Your Aadhaar is linked to money laundering. Stay on video call and transfer money to clear your name.",
            "You are under digital arrest. Do not disconnect and do not tell anyone. Send funds to the RBI verification account.",
        ),
    ),
    ScriptPattern(
        id="kyc_otp_takeover",
        label="KYC or OTP account takeover",
        severity="high",
        markers=(
            "kyc expired",
            "otp",
            "card blocked",
            "account blocked",
            "verify immediately",
            "share the code",
        ),
        templates=(
            "Your KYC has expired and your account will be blocked. Share the OTP to verify immediately.",
            "Your card is blocked. Tell us the code sent to your phone to reactivate it.",
        ),
    ),
    ScriptPattern(
        id="courier_seizure_v1",
        label="Courier parcel seizure threat",
        severity="high",
        markers=(
            "courier seized",
            "parcel seized",
            "customs",
            "narcotics",
            "case registered",
            "video statement",
        ),
        templates=(
            "Your courier parcel has been seized by customs and a narcotics case is registered. Join video statement now.",
        ),
    ),
    ScriptPattern(
        id="refund_remote_access",
        label="Refund or remote-access lure",
        severity="medium",
        markers=(
            "refund",
            "install app",
            "anydesk",
            "screen share",
            "upi pin",
            "collect request",
        ),
        templates=(
            "Install the support app and share your screen to receive the refund. Enter your UPI PIN to approve.",
        ),
    ),
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


def match_script(text: str) -> dict:
    """Return the strongest script match with explainable evidence."""
    lowered = (text or "").lower()
    text_tokens = _tokens(lowered)
    text_embed = llm.embed(lowered or "empty")
    best: dict | None = None

    for pattern in SCRIPT_PATTERNS:
        hits = [marker for marker in pattern.markers if marker in lowered]
        marker_score = len(hits) / max(4, len(pattern.markers) * 0.62)

        template_scores = []
        for template in pattern.templates:
            template_tokens = _tokens(template)
            overlap = len(text_tokens & template_tokens) / max(1, len(template_tokens))
            semantic = _cosine(text_embed, llm.embed(template))
            template_scores.append((overlap * 0.75) + (semantic * 0.25))

        template_score = max(template_scores or [0.0])
        score = min(0.99, max(marker_score, template_score))
        if hits and len(hits) >= 5:
            score = max(score, 0.98)

        candidate = {
            "pattern_id": pattern.id,
            "label": pattern.label,
            "severity": pattern.severity,
            "score": round(score, 2),
            "matched_markers": hits,
            "template_similarity": round(template_score, 2),
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate

    if not best or best["score"] < 0.25:
        return {
            "pattern_id": None,
            "label": None,
            "severity": "low",
            "score": 0.0,
            "matched_markers": [],
            "template_similarity": 0.0,
        }
    return best


def all_markers() -> list[str]:
    markers: list[str] = []
    for pattern in SCRIPT_PATTERNS:
        markers.extend(pattern.markers)
    return sorted(set(markers))
