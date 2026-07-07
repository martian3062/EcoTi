"""Watchdog — periodic health heartbeat (Celery beat task).

Marks unhealthy agents, "restarts" (re-instantiates) any that crashed and
pushes a self-heal toast to the dashboard. In this scaffold the heartbeat
simply confirms each registered agent is importable/instantiable; in P1+ it
pings live worker health.
"""
from __future__ import annotations

import logging

from celery import shared_task
from core import bus
from core.models import AgentHealth

logger = logging.getLogger("ecoti.watchdog")


@shared_task(name="orchestrator.watchdog.heartbeat")
def heartbeat() -> dict:
    from agents import AGENT_REGISTRY

    restarted = []
    for name, _spec in AGENT_REGISTRY.items():
        last = (
            AgentHealth.objects.filter(agent=name).order_by("-created_at").first()
        )
        if last and last.status == "crashed":
            # "Restart": the swarm factory is stateless, so re-registering is enough.
            AgentHealth.objects.create(
                agent=name, status="restarted", detail="watchdog respawned node"
            )
            bus.publish_toast(
                f"Watchdog restarted crashed agent '{name}'",
                level="info",
                extra={"agent": name},
            )
            restarted.append(name)
    return {"checked": list(AGENT_REGISTRY.keys()), "restarted": restarted}
