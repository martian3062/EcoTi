"""Digital footprint / OSINT aggregator (thin wrapper over the enricher registry).

Classifies an identifier (phone · email · UPI · IP · username) and delegates to
``core.osint.registry.aggregate``, which runs all applicable enrichers
concurrently — HIBP breach/stealer-logs, holehe account enum, DNS/MX/SPF,
Tor + IP geo/abuse, WhatsMyName username scan, fraud-graph linkage — then fuses
risk, builds an identity graph, caches, and emits A2A fusion events.
"""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UPI_RE = re.compile(r"^[\w.\-]{2,}@[a-zA-Z]{2,}$")  # handle@bank (no dot after @)
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,}$")
IPV4_RE = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")


def classify(identifier: str) -> str:
    s = (identifier or "").strip()
    m = IPV4_RE.match(s)
    if m and all(0 <= int(g) <= 255 for g in m.groups()):
        return "ip"
    if EMAIL_RE.match(s):
        return "email"
    if PHONE_RE.match(s) and sum(c.isdigit() for c in s) >= 7 and "@" not in s:
        return "phone"
    if UPI_RE.match(s):
        return "upi"
    return "username"


def build_footprint(identifier: str, lang: str = "en") -> dict:
    from .osint import aggregate

    return aggregate(identifier.strip(), classify(identifier), lang)
