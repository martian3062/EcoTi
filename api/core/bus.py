"""A2A event bus.

Publishes ``A2AEvent`` to two places:
  1. Redis pub/sub (so the correlator / watchdog / other workers can subscribe), and
  2. the Channels layer group ``feed`` (so the Next.js dashboard streams live).

Falls back to a pure in-process callback list when neither Redis nor Channels
is configured (used in unit tests).
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

from .events import A2AEvent, FusedTrustRisk

logger = logging.getLogger("ecoti.bus")

BUS_CHANNEL = "ecoti.a2a"          # Redis pub/sub channel
FEED_GROUP = "feed"               # Channels group for the dashboard

# In-process subscribers (tests / single-process mode).
_local_subscribers: list[Callable[[A2AEvent], None]] = []


def subscribe(callback: Callable[[A2AEvent], None]) -> None:
    _local_subscribers.append(callback)


def _redis_client():
    if not settings.REDIS_URL:
        return None
    try:
        import redis

        return redis.from_url(settings.REDIS_URL)
    except Exception as exc:  # pragma: no cover - infra optional
        logger.warning("Redis unavailable for bus: %s", exc)
        return None


def _push_to_feed(kind: str, data: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            FEED_GROUP, {"type": "feed.event", "kind": kind, "data": data}
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Channels push failed: %s", exc)


def publish(event: A2AEvent) -> None:
    """Publish a raw module event."""
    data = event.model_dump_jsonable()
    logger.info("A2A %s/%s conf=%.2f", event.module, event.signal, event.confidence)

    for cb in list(_local_subscribers):
        try:
            cb(event)
        except Exception:  # pragma: no cover
            logger.exception("subscriber failed")

    client = _redis_client()
    if client is not None:
        try:
            client.publish(BUS_CHANNEL, json.dumps({"kind": "event", "data": data}))
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis publish failed: %s", exc)

    _push_to_feed("event", data)


def publish_fused(risk: FusedTrustRisk) -> None:
    data = risk.model_dump_jsonable()
    logger.info("FUSED TrustRisk %s score=%.2f modules=%s",
                risk.identifier, risk.score, risk.modules)
    client = _redis_client()
    if client is not None:
        try:
            client.publish(BUS_CHANNEL, json.dumps({"kind": "fused", "data": data}))
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis fused publish failed: %s", exc)
    _push_to_feed("fused", data)


def publish_toast(message: str, level: str = "info", extra: dict | None = None) -> None:
    """Push a self-heal / system toast to the dashboard."""
    data = {"message": message, "level": level, **(extra or {})}
    _push_to_feed("toast", data)
