"""Ingestion: advisory text -> chunks -> embeddings -> DB."""
from __future__ import annotations

import re

from core import llm

from .firecrawl import scrape
from .models import AdvisoryChunk, AdvisorySource

_CHUNK_CHARS = 700


def chunk_text(text: str, size: int = _CHUNK_CHARS) -> list[str]:
    """Split on sentence boundaries into ~``size``-char chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > size and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += " " + s
    if cur.strip():
        chunks.append(cur.strip())
    return chunks or [text.strip()]


def ingest_document(*, title: str, authority: str, text: str, url: str = "",
                    origin: str = "seed") -> AdvisorySource:
    src = AdvisorySource.objects.create(
        title=title, authority=authority, url=url, origin=origin
    )
    for i, chunk in enumerate(chunk_text(text)):
        AdvisoryChunk.objects.create(
            source=src, ordinal=i, text=chunk, embedding=llm.embed(chunk)
        )
    return src


def ingest_url(url: str, *, title: str = "", authority: str = "") -> AdvisorySource | None:
    """Fetch a live advisory via Firecrawl and ingest it (needs FIRECRAWL_API_KEY)."""
    md = scrape(url)
    if not md:
        return None
    return ingest_document(
        title=title or url, authority=authority or "web", text=md,
        url=url, origin="firecrawl",
    )
