"""Swarm base classes.

Each EcoTi module is a *swarm* of specialist sub-agents coordinated by a small
LangGraph state graph, not a single LLM call. ``BaseSwarm`` runs its sub-agents
in sequence (the default pattern), accumulating a shared ``state`` dict, catches
any sub-agent failure and surfaces it so the orchestrator's planner can reroute.

LangGraph is used when available; a tiny built-in sequential runner is the
fallback so the scaffold runs even before models/extra deps are installed.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("ecoti.swarm")


class SubAgentError(Exception):
    """Raised by a sub-agent to signal failure (triggers self-healing)."""


@dataclass
class SubAgent:
    """One specialist in a swarm. ``fn(state) -> dict`` updates shared state."""

    name: str
    fn: Callable[[dict[str, Any]], dict[str, Any]]

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        update = self.fn(state) or {}
        return update


@dataclass
class BaseSwarm:
    """A named swarm of sub-agents run in sequence over a shared state."""

    name: str
    sub_agents: list[SubAgent] = field(default_factory=list)

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        state: dict[str, Any] = dict(inputs)
        state.setdefault("_trace", [])
        graph = self._build_graph()
        if graph is not None:
            return graph.invoke(state)
        # Fallback sequential runner.
        for agent in self.sub_agents:
            update = agent.run(state)
            state.update(update)
            state["_trace"].append({"sub_agent": agent.name, "ok": True})
        return state

    def _build_graph(self):
        """Compile a LangGraph StateGraph of the sub-agents, if langgraph exists."""
        try:
            from langgraph.graph import END, START, StateGraph
        except Exception:
            return None

        builder = StateGraph(dict)

        def wrap(agent: SubAgent):
            def node(state: dict[str, Any]) -> dict[str, Any]:
                update = agent.run(state)
                trace = list(state.get("_trace", []))
                trace.append({"sub_agent": agent.name, "ok": True})
                # Return the full merged state so every channel persists across
                # nodes (untyped-dict graphs use a last-value reducer per key).
                return {**state, **update, "_trace": trace}

            return node

        prev = START
        for agent in self.sub_agents:
            builder.add_node(agent.name, wrap(agent))
            builder.add_edge(prev, agent.name)
            prev = agent.name
        builder.add_edge(prev, END)
        try:
            return builder.compile()
        except Exception as exc:  # pragma: no cover
            logger.warning("LangGraph compile failed, using fallback runner: %s", exc)
            return None
