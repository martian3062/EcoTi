"""Mobile-number scam check.

Fuses EcoTi's own intelligence for a citizen-facing "is this number a scam?"
lookup:

  1. libphonenumber  — exact validity / region / carrier / line-type (VOIP = red flag)
  2. IPQualityScore   — real-time crowd-sourced fraud reputation (optional key)
  3. Fraud-graph      — mule-cluster linkage (self-healing)
  4. Reported history — past flagged TrustEvents / fused risks
  5. Community reports — citizen fraud reports (grows the watchlist)
  6. LLM advisory      — a short, localised safety note (Groq/Kimi + Sarvam)

Returns a combined verdict (safe / suspicious / scam) with explainable reasons.
"""
from __future__ import annotations

import re
from datetime import timedelta

from django.utils import timezone

from . import llm, phone_reputation

KNOWN_SCAM_NUMBERS = {"+919812345678"}


def normalize(raw: str) -> str:
    """Normalise to E.164 via libphonenumber when possible, else best-effort."""
    val = phone_reputation.validate(raw)
    if val.get("e164"):
        return val["e164"]
    s = re.sub(r"[^\d+]", "", raw or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+"):
        digits = re.sub(r"\D", "", s)
        if len(digits) == 10:
            s = "+91" + digits
        elif len(digits) == 12 and digits.startswith("91"):
            s = "+" + digits
        else:
            s = "+" + digits
    return s


def _heuristics(number: str, val: dict) -> tuple[float, list[str]]:
    reasons: list[str] = []
    risk = 0.0
    if number in KNOWN_SCAM_NUMBERS:
        return 0.9, ["Number is on a known fraud watchlist."]

    if val.get("available"):
        if val.get("valid") is False:
            risk = max(risk, 0.55)
            reasons.append("Not a valid phone number for its region (possible spoof).")
        line_type = val.get("line_type")
        if line_type == "voip":
            risk = max(risk, 0.6)
            reasons.append("VOIP line — heavily used by scam call-centres.")
        elif line_type in ("premium_rate", "shared_cost"):
            risk = max(risk, 0.5)
            reasons.append(f"{line_type.replace('_', ' ')} line — unusual for a genuine caller.")
        cc = val.get("country_code")
        if cc and cc != 91:
            risk = max(risk, 0.45)
            reasons.append(f"International number (+{cc}) — agencies never call citizens from abroad.")
        if val.get("carrier") or val.get("location"):
            reasons.append(
                f"Carrier: {val.get('carrier') or 'unknown'}"
                f"{' · ' + val['location'] if val.get('location') else ''}."
            )
    else:
        # libphonenumber unavailable — fall back to simple checks.
        digits = re.sub(r"\D", "", number)
        if number.startswith("+91") and len(digits) != 12:
            risk = max(risk, 0.5)
            reasons.append("Not a valid 10-digit Indian mobile number.")

    if not reasons:
        reasons.append("Number format and line type look normal.")
    return risk, reasons


def _reputation(e164: str, region: str) -> tuple[float, list[str], dict]:
    rep = phone_reputation.ipqs_lookup(e164, region or "IN")
    if not rep:
        return 0.0, [], {"available": False}
    reasons: list[str] = []
    risk = 0.0
    fs = rep.get("fraud_score")
    if isinstance(fs, (int, float)):
        risk = max(risk, fs / 100.0)
        reasons.append(f"Live reputation fraud score {fs}/100.")
    if rep.get("recent_abuse"):
        risk = max(risk, 0.85)
        reasons.append("Recent abuse reported for this number (live reputation).")
    if rep.get("spammer"):
        risk = max(risk, 0.75)
        reasons.append("Flagged as a spammer (live reputation).")
    if rep.get("voip"):
        risk = max(risk, 0.55)
    return risk, reasons, {"available": True, **rep}


def _community(number: str, e164: str) -> tuple[float, list[str], dict]:
    from .models import FraudReport

    variants = {number, e164}
    n = FraudReport.objects.filter(number__in=variants).count()
    if n >= 3:
        return 0.8, [f"Reported by {n} citizens as fraud (community watchlist)."], {"reports": n}
    if n >= 1:
        return 0.5, [f"Reported by {n} citizen(s) as fraud."], {"reports": n}
    return 0.0, [], {"reports": 0}


def _history(number: str) -> tuple[float, list[str], dict]:
    from .models import FusedTrustRiskRecord, TrustEvent

    reasons: list[str] = []
    risk = 0.0
    window = timezone.now() - timedelta(days=30)
    events = TrustEvent.objects.filter(identifier=number, ts__gte=window)
    scam_events = [e for e in events if e.confidence >= 0.6]
    modules = sorted({e.module for e in scam_events})
    if scam_events:
        risk = max(risk, min(0.95, max(e.confidence for e in scam_events)))
        reasons.append(f"Flagged {len(scam_events)}× in the last 30 days by: {', '.join(modules)}.")
    fused = FusedTrustRiskRecord.objects.filter(identifier=number).order_by("-ts").first()
    if fused:
        risk = max(risk, fused.score)
        reasons.append(f"Part of a fused TrustRisk ({len(fused.modules)} independent signals).")
    return risk, reasons, {"flagged_events": len(scam_events), "modules": modules, "fused": bool(fused)}


def _graph(number: str) -> tuple[float, list[str], dict]:
    try:
        from orchestrator import planner

        out = planner.run_agent("fraud_graph", {"identifier": number})
        payload = out.get("event").payload if out.get("event") else {}
        risk = float(payload.get("risk") or 0.0)
        size = payload.get("cluster_size") or 0
        districts = payload.get("linked_districts") or []
        stats = {"cluster_size": size, "districts": districts, "method": payload.get("method"),
                 "route": out.get("_route", "primary")}
        if risk >= 0.6 and size > 1:
            reasons = [
                f"Linked to a {size}-node mule cluster across {len(districts)} district(s)"
                f"{': ' + ', '.join(districts) if districts else ''}."
            ]
            return risk, reasons, stats
        return 0.0, [], stats
    except Exception:
        return 0.0, [], {}


def check_number(raw_number: str, lang: str = "en") -> dict:
    val = phone_reputation.validate(raw_number)
    number = normalize(raw_number)
    e164 = val.get("e164") or number
    region = val.get("region") or "IN"

    h_risk, h_reasons = _heuristics(number, val)
    rep_risk, rep_reasons, rep_stats = _reputation(e164, region)
    g_risk, g_reasons, g_stats = _graph(number)
    hist_risk, hist_reasons, hist_stats = _history(number)
    com_risk, com_reasons, com_stats = _community(number, e164)

    score = round(max(h_risk, rep_risk, g_risk, hist_risk, com_risk), 2)
    verdict = "scam" if score >= 0.6 else "suspicious" if score >= 0.3 else "safe"
    reasons = g_reasons + rep_reasons + com_reasons + hist_reasons + h_reasons

    actions = (
        [
            "Do not call back, share OTP, or transfer any money.",
            "Report the number on the 1930 cyber helpline / cybercrime.gov.in.",
            "Report it on Sanchar Saathi (Chakshu) so the SIM can be blocked.",
        ]
        if verdict != "safe"
        else ["No strong fraud signal found — stay alert and never share OTP or PIN."]
    )

    return {
        "number": number,
        "verdict": verdict,
        "risk_score": score,
        "reasons": reasons,
        "recommended_actions": actions,
        "advisory": _advisory(number, verdict, reasons, lang),
        "validation": {k: val.get(k) for k in ("valid", "line_type", "carrier", "location", "region", "country_code")},
        "signals": {
            "heuristic": round(h_risk, 2),
            "reputation": round(rep_risk, 2),
            "graph": round(g_risk, 2),
            "history": round(hist_risk, 2),
            "community": round(com_risk, 2),
        },
        "reputation": rep_stats,
        "graph": g_stats,
        "history": hist_stats,
        "community": com_stats,
        "lang": lang,
    }


def _advisory(number: str, verdict: str, reasons: list[str], lang: str) -> str:
    prompt = (
        f"A citizen is checking phone number {number}. Verdict: {verdict}. "
        f"Signals: {'; '.join(reasons)}. In one or two sentences, advise the citizen "
        f"what this means and the single most important next step."
    )
    text = llm.complete(
        prompt,
        system="You are EcoTi's number-safety advisor for India. Be brief, protective, cite 1930.",
    )
    if not text or text.startswith("[stub-verdict]"):
        if verdict == "scam":
            return ("High fraud risk. Do not engage — no agency arrests or demands money by phone. "
                    "Report on the 1930 helpline.")
        if verdict == "suspicious":
            return ("Some risk signals detected. Do not share OTP or money; verify via official "
                    "channels and report on 1930 if pressured.")
        return "No strong fraud signal found. Stay alert and never share OTP or PIN."
    if lang not in {"en", "en-IN"}:
        text = llm.translate(text, lang)
    return text.strip()
