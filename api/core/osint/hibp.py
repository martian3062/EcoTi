"""Have I Been Pwned enricher — real breach + stealer-log exposure for an email.

Uses the HIBP REST API v3 directly (production-safe; the MCP connector only
reaches the Claude session). Account lookups need ``HIBP_API_KEY`` (paid); when
unset the enricher self-skips cleanly — every other enricher still runs.
"""
from __future__ import annotations

import logging

import requests
from django.conf import settings

from core.events import A2AEvent
from .base import EnrichResult

logger = logging.getLogger("ecoti.osint.hibp")

_BASE = "https://haveibeenpwned.com/api/v3"
# Data classes that make a breach materially more dangerous for fraud.
_SENSITIVE = {"Passwords", "Credit cards", "Bank account numbers", "Government issued IDs",
              "Auth tokens", "Historical passwords", "Security questions and answers", "PINs"}


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    key = getattr(settings, "HIBP_API_KEY", "")
    if not key:
        return EnrichResult(findings=["Breach check skipped (no HIBP key)."], sources=[])

    headers = {"hibp-api-key": key, "user-agent": "EcoTi-OSINT"}
    res = EnrichResult(sources=["Have I Been Pwned"])
    try:
        r = requests.get(
            f"{_BASE}/breachedaccount/{requests.utils.quote(identifier)}",
            params={"truncateResponse": "false"}, headers=headers, timeout=15,
        )
        if r.status_code == 404:
            res.findings.append("No known breaches for this email (HIBP).")
            res.attributes["breaches"] = 0
            return res
        r.raise_for_status()
        breaches = r.json()
    except Exception as exc:  # pragma: no cover
        logger.warning("HIBP lookup failed: %s", exc)
        res.findings.append("Breach lookup unavailable right now.")
        return res

    n = len(breaches)
    sensitive = [b for b in breaches if _SENSITIVE & set(b.get("DataClasses", []))]
    res.attributes["breaches"] = n
    res.attributes["breach_names"] = [b.get("Name") for b in breaches][:20]
    res.attributes["breach_timeline"] = [
        {"name": b.get("Title") or b.get("Name"), "date": b.get("BreachDate"),
         "pwn_count": b.get("PwnCount"), "sensitive": bool(_SENSITIVE & set(b.get("DataClasses", []))),
         "classes": b.get("DataClasses", [])[:6]}
        for b in sorted(breaches, key=lambda b: b.get("BreachDate", ""), reverse=True)[:12]
    ]
    # risk scales with count + sensitivity
    res.risk = min(0.95, 0.25 + 0.06 * n + 0.15 * len(sensitive))
    res.findings.append(
        f"Exposed in {n} data breach(es)"
        + (f", {len(sensitive)} leaking passwords/financial/ID data" if sensitive else "") + "."
    )
    # graph: identifier -> each breach
    for b in breaches[:12]:
        bid = f"breach:{b.get('Name')}"
        res.nodes.append({"id": bid, "label": b.get("Title") or b.get("Name"), "type": "breach",
                          "risk": 0.8 if _SENSITIVE & set(b.get("DataClasses", [])) else 0.4})
        res.edges.append({"src": identifier, "dst": bid, "rel": "exposed_in"})

    # stealer logs (needs a subscription tier; skip quietly on 4xx)
    try:
        s = requests.get(f"{_BASE}/stealerlogsbyemailaddress/{requests.utils.quote(identifier)}",
                         headers=headers, timeout=12)
        if s.status_code == 200:
            domains = s.json() or []
            if domains:
                res.risk = max(res.risk, 0.9)
                res.attributes["stealer_log_domains"] = domains[:20]
                res.findings.append(
                    f"⚠ Credentials found in malware stealer logs for {len(domains)} site(s) — high takeover risk."
                )
    except Exception:  # pragma: no cover
        pass

    if res.risk >= 0.6:
        res.event = A2AEvent(
            module="osint", signal="breach_exposure", identifier=identifier,
            confidence=round(res.risk, 2),
            payload={"breaches": n, "sensitive": len(sensitive)},
        )
    return res
