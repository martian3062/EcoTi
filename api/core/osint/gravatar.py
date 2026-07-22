"""Gravatar presence enricher for an email (public web-presence signal)."""
from __future__ import annotations

import hashlib

import requests

from .base import EnrichResult


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    h = hashlib.md5(identifier.strip().lower().encode()).hexdigest()
    res = EnrichResult(sources=["Gravatar"], attributes={"gravatar_profile": f"https://gravatar.com/{h}"})
    exists = False
    try:
        r = requests.get(f"https://www.gravatar.com/avatar/{h}?d=404", timeout=8)
        exists = r.status_code == 200
    except Exception:
        pass
    res.attributes["gravatar"] = exists
    res.findings.append(
        "Public Gravatar profile exists (some web presence)." if exists
        else "No public Gravatar profile found."
    )
    if exists:
        res.nodes.append({"id": f"gravatar:{h[:8]}", "label": "Gravatar", "type": "account", "risk": 0.1})
        res.edges.append({"src": identifier, "dst": f"gravatar:{h[:8]}", "rel": "account_on"})
    return res
