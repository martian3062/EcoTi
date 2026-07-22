"""UPI enricher — PSP/bank parse + embedded-number fraud-graph linkage."""
from __future__ import annotations

import re

from .base import EnrichResult

UPI_BANKS = {
    "okhdfcbank": "HDFC Bank", "oksbi": "State Bank of India", "okaxis": "Axis Bank",
    "okicici": "ICICI Bank", "ybl": "PhonePe (Yes Bank)", "paytm": "Paytm",
    "apl": "Amazon Pay", "ibl": "PhonePe (IDFC)", "axl": "Axis / Google Pay",
}


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    handle, bank_code = identifier.split("@", 1)
    bank = UPI_BANKS.get(bank_code.lower(), f"Unknown PSP ({bank_code})")
    res = EnrichResult(sources=["UPI PSP map", "EcoTi fraud-graph"],
                       findings=[f"UPI handle on {bank}."],
                       attributes={"handle": handle, "bank": bank})
    phone_like = re.sub(r"\D", "", handle)
    res.attributes["embedded_number"] = phone_like or None
    if len(phone_like) == 10:
        from core.number_intel import check_number

        chk = check_number("+91" + phone_like, ctx.get("lang", "en"))
        res.risk = chk["risk_score"]
        res.findings.append(f"Embedded number +91{phone_like}: {chk['verdict']} ({chk['risk_score']}).")
        res.findings += chk["reasons"][:2]
        res.detail["number"] = chk
        for d in chk.get("graph", {}).get("districts", []):
            res.nodes.append({"id": f"district:{d}", "label": d, "type": "district", "risk": 0.6})
            res.edges.append({"src": identifier, "dst": f"district:{d}", "rel": "mules_in"})
        if chk["risk_score"] >= 0.6:
            from core.events import A2AEvent

            res.event = A2AEvent(module="osint", signal="scam_upi", identifier=identifier,
                                confidence=chk["risk_score"], payload={"bank": bank})
    return res
