"""Enricher result contract shared by every OSINT source."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.events import A2AEvent


@dataclass
class EnrichResult:
    """What one enricher contributes to a footprint."""

    risk: float = 0.0
    findings: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    nodes: list[dict] = field(default_factory=list)   # graph nodes {id,label,type,risk}
    edges: list[dict] = field(default_factory=list)   # graph edges {src,dst,rel}
    event: A2AEvent | None = None                     # optional A2A fusion signal
    detail: dict[str, Any] = field(default_factory=dict)


# Registered as (name, kinds, fn). fn(identifier, ctx) -> EnrichResult.
Ctx = dict  # {"lang": str, "kind": str}
