"""Correlator + escalation gate.

Buffers module events by identifier (phone / UPI handle / device) in a short
window. When >= ``FUSION_MIN_SIGNALS`` *independent* modules cross the
confidence threshold for the same identifier, it emits one fused ``TrustRisk``
and triggers downstream responses:

  * citizen_shield  -> alert the victim
  * geo_command     -> map pulse
  * an EvidencePacket draft, gated behind human approval.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from core import bus
from core.events import A2AEvent, FusedTrustRisk
from core.models import EvidencePacket, FusedTrustRiskRecord, TrustEvent
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("ecoti.correlator")


def ingest(event: A2AEvent) -> FusedTrustRisk | None:
    """Persist an event and attempt fusion for its identifier."""
    TrustEvent.objects.create(
        module=event.module,
        signal=event.signal,
        identifier=event.identifier or "",
        confidence=event.confidence,
        route=event.route,
        payload=event.payload,
        ts=event.ts,
    )
    bus.publish(event)

    if not event.identifier:
        return None
    return _try_fuse(event.identifier)


def _try_fuse(identifier: str) -> FusedTrustRisk | None:
    window_start = timezone.now() - timedelta(seconds=settings.FUSION_WINDOW_SECONDS)
    recent = TrustEvent.objects.filter(
        identifier=identifier,
        ts__gte=window_start,
        confidence__gte=settings.FUSION_CONFIDENCE_THRESHOLD,
    ).exclude(module="orchestrator")

    # Independent signals = distinct modules above threshold.
    by_module: dict[str, TrustEvent] = {}
    for te in recent:
        cur = by_module.get(te.module)
        if cur is None or te.confidence > cur.confidence:
            by_module[te.module] = te

    if len(by_module) < settings.FUSION_MIN_SIGNALS:
        return None

    # Avoid re-firing for the same identifier within the window.
    already = FusedTrustRiskRecord.objects.filter(
        identifier=identifier, ts__gte=window_start
    ).exists()
    if already:
        return None

    signals = [
        A2AEvent(
            module=te.module,
            signal=te.signal,
            payload=te.payload,
            confidence=te.confidence,
            ts=te.ts,
            identifier=identifier,
            route=te.route,
        )
        for te in by_module.values()
    ]
    score = min(0.99, sum(s.confidence for s in signals) / len(signals) + 0.1 * (len(signals) - 1))
    risk = FusedTrustRisk(identifier=identifier, signals=signals, score=score)

    record = FusedTrustRiskRecord.objects.create(
        identifier=identifier,
        score=score,
        modules=risk.modules,
        signals=[s.model_dump_jsonable() for s in signals],
        ts=risk.ts,
    )
    bus.publish_fused(risk)
    _escalate(record, risk)
    return risk


def _escalate(record: FusedTrustRiskRecord, risk: FusedTrustRisk) -> None:
    """Fire downstream responses behind the human-approval gate."""
    EvidencePacket.objects.create(
        fused_risk=record,
        identifier=risk.identifier,
        title=f"Fraud evidence packet — {risk.identifier}",
        body={
            "identifier": risk.identifier,
            "fused_score": risk.score,
            "modules": risk.modules,
            "signals": [s.model_dump_jsonable() for s in risk.signals],
            "drafted_at": risk.ts.isoformat(),
            "destination": "I4C / MHA",
        },
        status="pending_approval",
    )
    bus.publish_toast(
        f"⚠ Fused TrustRisk on {risk.identifier} ({len(risk.modules)} signals) "
        f"→ Shield alerted, evidence packet drafted (awaiting approval)",
        level="critical",
        extra={"identifier": risk.identifier},
    )
