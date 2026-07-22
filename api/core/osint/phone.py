"""Phone enricher — wraps the multi-signal number check + mule-cluster graph."""
from __future__ import annotations

from core.events import A2AEvent
from .base import EnrichResult


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    from core.number_intel import check_number

    chk = check_number(identifier, ctx.get("lang", "en"))
    res = EnrichResult(risk=chk["risk_score"], findings=list(chk["reasons"]))
    res.sources = ["libphonenumber", "EcoTi fraud-graph", "reported history", "community reports"]
    if chk.get("reputation", {}).get("available"):
        res.sources.append("IPQualityScore")
    res.attributes = {
        "line_type": chk["validation"].get("line_type"),
        "carrier": chk["validation"].get("carrier"),
        "region": chk["validation"].get("region"),
        "valid": chk["validation"].get("valid"),
        "mule_cluster": chk["graph"].get("cluster_size"),
        "districts": chk["graph"].get("districts"),
    }
    res.detail = chk
    # graph: number -> mule cluster
    cluster = chk.get("graph", {})
    if (cluster.get("cluster_size") or 0) > 1:
        for d in cluster.get("districts", []):
            res.nodes.append({"id": f"district:{d}", "label": d, "type": "district", "risk": 0.6})
            res.edges.append({"src": identifier, "dst": f"district:{d}", "rel": "mules_in"})
    if chk["risk_score"] >= 0.6:
        res.event = A2AEvent(module="osint", signal="scam_number", identifier=chk["number"],
                            confidence=chk["risk_score"], payload={"verdict": chk["verdict"]})
    return res
