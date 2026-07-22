"""Live fraud/cyber news feed — pulls real headlines from Google News RSS.

Themed to EcoTi (digital-arrest scams, UPI/cyber fraud, RBI/I4C alerts). Cached
in-process for a few minutes to stay well within rate limits. Powers the
TV-style live ticker on the dashboard.
"""
from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

logger = logging.getLogger("ecoti.news")

_RSS = "https://news.google.com/rss/search"
_QUERIES = [
    "digital arrest scam India",
    "cyber fraud India cybercrime",
    "UPI fraud OR online scam India",
    "RBI OR I4C fraud warning India",
]
_UA = {"User-Agent": "Mozilla/5.0 (EcoTi-NewsTicker)"}
_TTL = 600  # 10 min
_cache: dict = {"ts": 0.0, "items": []}

_FALLBACK = [
    {"title": "Stay alert: no agency arrests over video call — report scams on 1930", "source": "I4C", "link": "https://cybercrime.gov.in/", "ts": ""},
    {"title": "RBI: never share OTP, PIN or KYC details over calls or links", "source": "RBI", "link": "https://www.rbi.org.in/", "ts": ""},
    {"title": "Report suspicious numbers on Sanchar Saathi (Chakshu)", "source": "DoT", "link": "https://sancharsaathi.gov.in/", "ts": ""},
]


def _parse(xml_bytes: bytes) -> list[dict]:
    out = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        src_el = item.find("source")
        source = (src_el.text if src_el is not None else "") or ""
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)].strip()
        try:
            ts = parsedate_to_datetime(pub)
        except Exception:
            ts = None
        if title:
            out.append({"title": title, "source": source, "link": link,
                        "ts": ts.isoformat() if ts else "", "_sort": ts.timestamp() if ts else 0})
    return out


def headlines(limit: int = 24) -> list[dict]:
    now = time.time()
    if _cache["items"] and now - _cache["ts"] < _TTL:
        return _cache["items"][:limit]

    items: list[dict] = []
    seen = set()
    try:
        for q in _QUERIES:
            r = requests.get(_RSS, params={"q": q, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
                             headers=_UA, timeout=12)
            r.raise_for_status()
            for it in _parse(r.content):
                key = it["title"].lower()[:80]
                if key in seen:
                    continue
                seen.add(key)
                items.append(it)
    except Exception as exc:  # pragma: no cover - network optional
        logger.warning("news fetch failed: %s", exc)

    if items:
        items.sort(key=lambda x: x.get("_sort", 0), reverse=True)
        for it in items:
            it.pop("_sort", None)
        _cache.update(ts=now, items=items)
        return items[:limit]

    return _cache["items"][:limit] or _FALLBACK


_anchor = {"ts": 0.0, "data": None}
_ANCHOR_FALLBACK = (
    "Good day — this is EcoTi AI TV with your fraud watch. Digital-arrest and UPI "
    "scams continue to target citizens across India. Remember: no real agency arrests "
    "anyone over a video call, and never share an OTP or KYC detail. If in doubt, "
    "disconnect and report it on the 1930 cyber helpline. Stay alert, stay safe."
)


def anchor_bulletin() -> dict:
    """An LLM-written news-anchor bulletin summarising the top fraud headlines."""
    now = time.time()
    if _anchor["data"] and now - _anchor["ts"] < _TTL:
        return _anchor["data"]

    items = headlines(6)
    top = "; ".join(i["title"] for i in items[:5]) or "cyber and UPI fraud in India"
    try:
        from . import llm

        script = llm.complete(
            f"Summarise these India fraud/cyber news headlines into a 45-65 word spoken TV "
            f"news bulletin for ordinary citizens — calm, clear, no jargon — and end with ONE "
            f"safety tip that mentions the 1930 cyber helpline. Headlines: {top}",
            system="You are 'EcoTi AI TV', a concise fraud-safety news anchor for India.",
        )
    except Exception:  # pragma: no cover
        script = ""
    if not script or script.startswith("[stub"):
        script = _ANCHOR_FALLBACK

    data = {"script": script.strip(), "headlines": items[:5]}
    _anchor.update(ts=now, data=data)
    return data
