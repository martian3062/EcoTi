"""Username OSINT — real cross-platform presence check.

Replaces the naive "no automated lookups" username footprint with a curated,
WhatsMyName-style checker: a set of platforms with per-site match signatures,
queried concurrently with short timeouts. Only checks whether a *public* profile
URL exists (standard OSINT) — no scraping of private data.

Curated for reliability (status-code / string signatures that don't false-positive
behind SPAs or aggressive bot-walls). Extend from the full WhatsMyName wmn-data.json
by adding entries below.
"""
from __future__ import annotations

import concurrent.futures
import logging
import re

import requests

logger = logging.getLogger("ecoti.username")

_UA = {"User-Agent": "Mozilla/5.0 (EcoTi-OSINT) Safari/537.36"}
_VALID = re.compile(r"^[A-Za-z0-9._-]{2,40}$")

# WhatsMyName-style signatures. found = status == e_code (and e_string present if
# given); m_string, if present in body, forces not-found.
SITES: list[dict] = [
    {"name": "GitHub", "cat": "coding", "uri": "https://github.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "GitLab", "cat": "coding", "uri": "https://gitlab.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "Reddit", "cat": "social", "uri": "https://www.reddit.com/user/{u}/about.json", "e_code": 200, "m_code": 404},
    {"name": "Medium", "cat": "blog", "uri": "https://medium.com/@{u}", "e_code": 200, "m_code": 404},
    {"name": "Dev.to", "cat": "coding", "uri": "https://dev.to/{u}", "e_code": 200, "m_code": 404},
    {"name": "Keybase", "cat": "coding", "uri": "https://keybase.io/{u}", "e_code": 200, "m_code": 404},
    {"name": "npm", "cat": "coding", "uri": "https://www.npmjs.com/~{u}", "e_code": 200, "m_code": 404},
    {"name": "PyPI", "cat": "coding", "uri": "https://pypi.org/user/{u}/", "e_code": 200, "m_code": 404},
    {"name": "Docker Hub", "cat": "coding", "uri": "https://hub.docker.com/v2/users/{u}/", "e_code": 200, "m_code": 404},
    {"name": "Replit", "cat": "coding", "uri": "https://replit.com/@{u}", "e_code": 200, "m_code": 404},
    {"name": "Kaggle", "cat": "data", "uri": "https://www.kaggle.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "SoundCloud", "cat": "music", "uri": "https://soundcloud.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "Vimeo", "cat": "video", "uri": "https://vimeo.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "Pinterest", "cat": "social", "uri": "https://www.pinterest.com/{u}/", "e_code": 200, "m_code": 404},
    {"name": "About.me", "cat": "social", "uri": "https://about.me/{u}", "e_code": 200, "m_code": 404},
    {"name": "Chess.com", "cat": "gaming", "uri": "https://www.chess.com/member/{u}", "e_code": 200, "m_code": 404},
    {"name": "HackerNews", "cat": "coding", "uri": "https://news.ycombinator.com/user?id={u}", "e_code": 200, "m_string": "No such user."},
    {"name": "Gravatar", "cat": "identity", "uri": "https://gravatar.com/{u}", "e_code": 200, "m_code": 404},
    {"name": "ProductHunt", "cat": "startup", "uri": "https://www.producthunt.com/@{u}", "e_code": 200, "m_code": 404},
    {"name": "Telegram", "cat": "messaging", "uri": "https://t.me/{u}", "e_code": 200, "m_string": "tgme_page_icon"},
    {"name": "Wattpad", "cat": "blog", "uri": "https://www.wattpad.com/user/{u}", "e_code": 200, "m_code": 404},
    {"name": "Buymeacoffee", "cat": "money", "uri": "https://www.buymeacoffee.com/{u}", "e_code": 200, "m_code": 404},
]


def _check(site: dict, account: str, timeout: float = 4.0) -> dict | None:
    url = site["uri"].format(u=account)
    try:
        r = requests.get(url, headers=_UA, timeout=timeout, allow_redirects=True)
    except Exception:
        return None
    found = r.status_code == site.get("e_code", 200)
    if found and site.get("e_string"):
        found = site["e_string"] in r.text
    if found and site.get("m_string") and site["m_string"] in r.text:
        found = False
    if not found:
        return None
    return {"site": site["name"], "category": site["cat"], "url": url}


def scan(username: str, timeout: float = 4.0, max_workers: int = 12) -> dict:
    """Return platforms where the username has a public profile."""
    if not _VALID.match(username or ""):
        return {"username": username, "valid": False, "checked": 0, "hits": []}
    hits: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_check, s, username, timeout): s for s in SITES}
        for fut in concurrent.futures.as_completed(futures, timeout=timeout + 6):
            try:
                res = fut.result()
                if res:
                    hits.append(res)
            except Exception:
                pass
    hits.sort(key=lambda h: h["site"])
    return {"username": username, "valid": True, "checked": len(SITES), "hits": hits}
