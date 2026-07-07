"""Typed A2A (agent-to-agent) event schema — the contract on the bus.

Every swarm emits an ``A2AEvent`` exactly as described in the blueprint:
``{module, signal, payload, confidence, ts}``. The orchestrator correlates
these and may emit a single fused ``FusedTrustRisk``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Module(str, Enum):
    SCAM_CALL = "scam_call"
    COUNTERFEIT_VISION = "counterfeit_vision"
    FRAUD_GRAPH = "fraud_graph"
    GEO_COMMAND = "geo_command"
    CITIZEN_SHIELD = "citizen_shield"
    ORCHESTRATOR = "orchestrator"


class A2AEvent(BaseModel):
    """The single event type that flows on the A2A bus."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    module: str
    signal: str
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    ts: datetime = Field(default_factory=_now)
    # The identifier the orchestrator correlates on (phone / UPI handle / device).
    identifier: str | None = None
    # "cloud" or "edge" — records which compute tier produced this.
    route: str = "cloud"

    def model_dump_jsonable(self) -> dict[str, Any]:
        d = self.model_dump()
        d["ts"] = self.ts.isoformat()
        return d


class FusedTrustRisk(BaseModel):
    """Emitted by the correlator when >= N independent signals cross threshold."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    identifier: str
    signals: list[A2AEvent]
    score: float
    ts: datetime = Field(default_factory=_now)

    @property
    def modules(self) -> list[str]:
        return sorted({s.module for s in self.signals})

    def model_dump_jsonable(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "identifier": self.identifier,
            "score": self.score,
            "modules": self.modules,
            "signals": [s.model_dump_jsonable() for s in self.signals],
            "ts": self.ts.isoformat(),
        }
