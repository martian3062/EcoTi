"""IP enricher — Tor exit/relay (reuses tor_intel) + free geo/abuse reputation."""
from __future__ import annotations

import logging

import requests
from django.conf import settings

from core.events import A2AEvent
from .base import EnrichResult

logger = logging.getLogger("ecoti.osint.ip")


def _geo(ip: str) -> dict:
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,regionName,city,isp,org,as,proxy,hosting"},
            timeout=8,
        )
        d = r.json()
        return d if d.get("status") == "success" else {}
    except Exception:
        return {}


def _abuse(ip: str) -> dict | None:
    key = getattr(settings, "ABUSEIPDB_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={"Key": key, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90}, timeout=10,
        )
        return r.json().get("data")
    except Exception:  # pragma: no cover
        return None


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    from core import tor_intel

    res = EnrichResult(sources=["Tor Onionoo", "ip-api geo"])
    tor = tor_intel.check_ip(identifier)
    if tor.get("is_tor"):
        res.risk = 0.9 if tor.get("bad_exit") else (0.75 if tor.get("is_exit") else 0.5)
        res.findings.append(
            f"IP is a Tor {'EXIT' if tor.get('is_exit') else 'relay'} node "
            f"({tor.get('nickname')}, {tor.get('country')}, {tor.get('as_name')})."
            + (" Flagged BadExit (malicious)." if tor.get("bad_exit") else "")
        )
        res.attributes.update({"is_tor": True, "is_exit": tor.get("is_exit"), "bad_exit": tor.get("bad_exit")})
        res.nodes.append({"id": "tor", "label": "Tor network", "type": "tor", "risk": 0.8})
        res.edges.append({"src": identifier, "dst": "tor", "rel": "exits_via"})
    elif tor.get("available"):
        res.attributes["is_tor"] = False
        res.findings.append("Not a known Tor relay/exit node.")

    geo = _geo(identifier)
    if geo:
        res.attributes.update({"country": geo.get("country"), "isp": geo.get("isp"),
                               "org": geo.get("org"), "asn": geo.get("as"),
                               "hosting": geo.get("hosting"), "proxy": geo.get("proxy")})
        res.findings.append(f"Geo: {geo.get('city') or ''} {geo.get('country') or ''} · {geo.get('isp') or geo.get('org')}.".strip())
        if geo.get("proxy"):
            res.risk = max(res.risk, 0.55)
            res.findings.append("Flagged as proxy/VPN (ip-api).")
        if geo.get("hosting"):
            res.findings.append("Hosting/datacenter IP (not residential).")

    ab = _abuse(identifier)
    if ab:
        score = ab.get("abuseConfidenceScore", 0)
        res.attributes["abuse_score"] = score
        res.sources.append("AbuseIPDB")
        if score:
            res.risk = max(res.risk, score / 100.0)
            res.findings.append(f"AbuseIPDB confidence {score}/100 ({ab.get('totalReports', 0)} reports).")

    if res.risk >= 0.6:
        res.event = A2AEvent(module="osint", signal="tor_exit" if tor.get("is_tor") else "bad_ip",
                            identifier=identifier, confidence=round(res.risk, 2),
                            payload={"country": res.attributes.get("country")})
    return res
