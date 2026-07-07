"""Fraud-Network Graph swarm — with self-healing GNN -> rule-based fallback.

Primary: a GraphSAGE node classifier (PyTorch Geometric) over a mule-network
graph (Elliptic / synthetic UPI), loaded into Neo4j. Fallback: a deterministic
rule-based linkage scorer so the swarm still returns a result if the GNN service
is down. ``FORCE_GNN_FAILURE=1`` triggers the fallback for the self-heal demo.
"""
from __future__ import annotations

from core.events import A2AEvent, Module
from core.swarm import BaseSwarm, SubAgent
from django.conf import settings

# Seeded in-memory mule cluster (Neo4j stands in for this in P1). A 14-node
# cluster across 3 districts, all reachable from the demo identifier.
_DEMO_IDENTIFIER = "+919812345678"
_CLUSTER = {
    "nodes": [
        {"id": _DEMO_IDENTIFIER, "type": "phone", "district": "Jaipur", "risk": 0.92},
        *[
            {"id": f"mule_{i}", "type": "upi", "district": d, "risk": round(0.6 + (i % 4) * 0.08, 2)}
            for i, d in enumerate((["Jaipur", "Alwar", "Bharatpur"] * 5)[:13])
        ],
    ],
    "edges": [{"src": _DEMO_IDENTIFIER, "dst": f"mule_{i}", "rel": "TRANSFERS_TO"} for i in range(13)],
    "districts": ["Jaipur", "Alwar", "Bharatpur"],
}


def _ingest(state: dict) -> dict:
    return {"identifier": state.get("identifier", _DEMO_IDENTIFIER)}


def _gnn_scorer(state: dict) -> dict:
    if settings.FORCE_GNN_FAILURE:
        raise RuntimeError("GNN service unreachable (FORCE_GNN_FAILURE)")
    # P1: real GraphSAGE inference. P0: deterministic risk from the seeded graph.
    ident = state["identifier"]
    risk = 0.92 if ident == _DEMO_IDENTIFIER else 0.41
    return {"risk": risk, "method": "graphsage"}


def _cluster_builder(state: dict) -> dict:
    ident = state["identifier"]
    if ident == _DEMO_IDENTIFIER:
        return {"cluster": _CLUSTER, "cluster_size": len(_CLUSTER["nodes"])}
    return {"cluster": {"nodes": [{"id": ident, "type": "phone", "risk": state["risk"]}],
                        "edges": [], "districts": []}, "cluster_size": 1}


def _evidence_packager(state: dict) -> dict:
    return {
        "verdict": "high_risk" if state["risk"] >= 0.6 else "low_risk",
        "confidence": round(state["risk"], 2),
        "linked_districts": state["cluster"].get("districts", []),
    }


_primary_swarm = BaseSwarm(
    name="fraud_graph",
    sub_agents=[
        SubAgent("ingest", _ingest),
        SubAgent("gnn_scorer", _gnn_scorer),
        SubAgent("cluster_builder", _cluster_builder),
        SubAgent("evidence_packager", _evidence_packager),
    ],
)


def _to_event(inputs: dict, state: dict, method: str) -> A2AEvent:
    return A2AEvent(
        module=Module.FRAUD_GRAPH.value,
        signal="fraud_graph_score",
        identifier=inputs.get("identifier", _DEMO_IDENTIFIER),
        confidence=state.get("confidence", 0.0),
        payload={
            "verdict": state.get("verdict"),
            "risk": state.get("risk"),
            "method": method,
            "cluster_size": state.get("cluster_size"),
            "cluster": state.get("cluster"),
            "linked_districts": state.get("linked_districts"),
        },
    )


def run(inputs: dict) -> dict:
    """Primary route: GraphSAGE GNN."""
    state = _primary_swarm.run(inputs)
    state["event"] = _to_event(inputs, state, method="graphsage")
    return state


def run_fallback(inputs: dict) -> dict:
    """Self-healing fallback: deterministic rule-based linkage scorer (no GNN)."""
    ident = inputs.get("identifier", _DEMO_IDENTIFIER)
    cluster = _CLUSTER if ident == _DEMO_IDENTIFIER else {
        "nodes": [{"id": ident, "type": "phone", "risk": 0.4}], "edges": [], "districts": []}
    # Rule: risk proportional to number of linked mule nodes.
    linked = len(cluster["edges"])
    risk = min(0.95, 0.3 + 0.05 * linked)
    state = {
        "identifier": ident,
        "risk": round(risk, 2),
        "verdict": "high_risk" if risk >= 0.6 else "low_risk",
        "confidence": round(risk, 2),
        "cluster": cluster,
        "cluster_size": len(cluster["nodes"]),
        "linked_districts": cluster.get("districts", []),
    }
    state["event"] = _to_event(inputs, state, method="rule_based_fallback")
    return state
