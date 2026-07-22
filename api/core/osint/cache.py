"""DB-backed TTL cache for OSINT lookups (respects external API rate limits)."""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def _ttl() -> int:
    return int(getattr(settings, "OSINT_CACHE_TTL", 21600))


def get(kind: str, identifier: str) -> dict | None:
    from core.models import OsintCache

    row = OsintCache.objects.filter(kind=kind, identifier=identifier).order_by("-created_at").first()
    if not row:
        return None
    if row.created_at < timezone.now() - timedelta(seconds=_ttl()):
        return None
    return row.payload


def set(kind: str, identifier: str, payload: dict) -> None:
    from core.models import OsintCache

    OsintCache.objects.update_or_create(
        kind=kind, identifier=identifier, defaults={"payload": payload, "created_at": timezone.now()}
    )
