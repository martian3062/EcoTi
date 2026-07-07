"""Minimal Firecrawl client (scrape URL -> markdown) using plain requests.

Only used when ``FIRECRAWL_API_KEY`` is set; the RAG corpus otherwise falls
back to the bundled advisories in ``corpus.py``.
"""
from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger("ecoti.firecrawl")

_API = "https://api.firecrawl.dev/v1/scrape"


def is_enabled() -> bool:
    return bool(getattr(settings, "FIRECRAWL_API_KEY", ""))


def scrape(url: str) -> str | None:
    """Return the page's markdown content, or None on failure."""
    if not is_enabled():
        return None
    try:
        resp = requests.post(
            _API,
            headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"},
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("markdown") or data.get("markdown")
    except Exception as exc:  # pragma: no cover - network optional
        logger.warning("Firecrawl scrape failed for %s: %s", url, exc)
        return None
