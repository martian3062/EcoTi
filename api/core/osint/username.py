"""Username enricher — wraps the WhatsMyName-style cross-platform scan."""
from __future__ import annotations

from .base import EnrichResult


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    from core import username_osint

    scan = username_osint.scan(identifier)
    hits = scan.get("hits", [])
    res = EnrichResult(sources=["WhatsMyName-style username scan"])
    res.attributes.update({"profiles_found": len(hits), "platforms_checked": scan.get("checked", 0)})
    if not scan.get("valid"):
        res.findings.append("Not a valid username format.")
        return res
    if hits:
        sites = ", ".join(h["site"] for h in hits[:12])
        res.findings.append(f"Public profile on {len(hits)} platform(s): {sites}.")
        for h in hits[:16]:
            nid = f"site:{h['site']}"
            res.nodes.append({"id": nid, "label": h["site"], "type": "platform", "risk": 0.15})
            res.edges.append({"src": identifier, "dst": nid, "rel": "profile_on"})
    else:
        res.findings.append(f"No public profile across {scan.get('checked', 0)} platforms.")
    res.detail["profiles"] = hits
    return res
