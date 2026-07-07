"""Self-healing planner.

Runs an agent swarm via its primary route. On any failure it looks up the
agent's registered *fallback* in ``AGENT_REGISTRY`` (e.g. fraud_graph GNN ->
rule-based; cloud -> edge), reroutes to it, logs the reroute as ``AgentHealth``
and pushes a self-heal toast to the dashboard. The citizen is never left
unprotected.
"""
from __future__ import annotations

import logging
from typing import Any

from core import bus
from core.models import AgentHealth

logger = logging.getLogger("ecoti.planner")


def run_agent(name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute an agent with self-healing fallback. Returns the result dict."""
    from agents import AGENT_REGISTRY  # late import avoids app-loading cycle

    spec = AGENT_REGISTRY.get(name)
    if spec is None:
        raise KeyError(f"Unknown agent '{name}'")

    primary = spec["primary"]
    try:
        result = primary(inputs)
        AgentHealth.objects.create(agent=name, status="healthy", detail="primary route ok")
        result.setdefault("_route", "primary")
        return result
    except Exception as exc:
        logger.warning("Agent %s primary route failed: %s", name, exc)
        fallback = spec.get("fallback")
        if fallback is None:
            AgentHealth.objects.create(agent=name, status="crashed", detail=str(exc)[:280])
            bus.publish_toast(
                f"Agent '{name}' failed with no fallback", level="error", extra={"agent": name}
            )
            raise

        fallback_name = spec.get("fallback_name", "fallback")
        AgentHealth.objects.create(
            agent=name,
            status="degraded",
            detail=f"primary failed: {str(exc)[:200]}",
            fallback_used=fallback_name,
        )
        bus.publish_toast(
            f"Agent '{name}' failed → rerouted to {fallback_name}",
            level="warning",
            extra={"agent": name, "fallback": fallback_name},
        )
        result = fallback(inputs)
        result.setdefault("_route", "fallback")
        result["_fallback_used"] = fallback_name
        return result
