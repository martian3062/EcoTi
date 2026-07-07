"""Agent registry.

Maps each module name to its primary route and (optionally) a self-healing
fallback. The planner uses this to run agents and reroute on failure; the
watchdog uses it to enumerate nodes for health checks.
"""
from . import (
    citizen_shield,
    counterfeit_vision,
    fraud_graph,
    geo_command,
    scam_call,
)

AGENT_REGISTRY = {
    "scam_call": {"primary": scam_call.run, "fallback": None},
    "counterfeit_vision": {"primary": counterfeit_vision.run, "fallback": None},
    "fraud_graph": {
        "primary": fraud_graph.run,
        "fallback": fraud_graph.run_fallback,
        "fallback_name": "rule_based_linkage",
    },
    "geo_command": {"primary": geo_command.run, "fallback": None},
    "citizen_shield": {"primary": citizen_shield.run, "fallback": None},
}

__all__ = ["AGENT_REGISTRY"]
