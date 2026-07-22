"""holehe enricher — which sites have an account registered to this email.

Runs a curated subset of holehe modules concurrently with a hard timeout.
ToS-adjacent + flaky, so it is fully optional: any import/runtime failure yields
an empty result and the rest of the footprint is unaffected.
"""
from __future__ import annotations

import logging

from .base import EnrichResult

logger = logging.getLogger("ecoti.osint.holehe")

# Curated, generally-reliable modules (short names). Extend freely.
_ALLOW = {
    "instagram", "twitter", "pinterest", "snapchat", "tumblr", "wordpress", "gravatar",
    "imgur", "adobe", "spotify", "discord", "amazon", "patreon", "atlassian", "aboutme",
    "codepen", "replit", "lastpass", "protonmail", "trello", "bitmoji", "strava",
    "rambler", "archive", "envato", "freelancer", "nike", "pornhub", "chess", "vsco",
    "wattpad", "coil", "buymeacoffee", "teamleader", "quora", "myspace", "samsung",
}
_TIMEOUT = 14


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    res = EnrichResult(sources=["holehe (account enumeration)"])
    try:
        import trio  # noqa: F401
        from holehe.core import import_submodules
    except Exception as exc:  # pragma: no cover
        logger.warning("holehe unavailable: %s", exc)
        return res

    try:
        mods = import_submodules("holehe.modules")
        selected = [fn for name, fn in _selected_callables(mods)]
        hits = _run(identifier, selected)
    except Exception as exc:  # pragma: no cover
        logger.warning("holehe run failed: %s", exc)
        return res

    used = [h for h in hits if h.get("exists")]
    res.attributes["accounts_found"] = len(used)
    res.attributes["accounts_checked"] = len(selected)
    if used:
        names = ", ".join(sorted({h["name"] for h in used}))[:200]
        res.findings.append(f"Email is registered on {len(used)} site(s): {names}.")
        for h in used[:14]:
            nid = f"acct:{h['name']}"
            res.nodes.append({"id": nid, "label": h["name"], "type": "account", "risk": 0.2})
            res.edges.append({"src": identifier, "dst": nid, "rel": "account_on"})
    else:
        res.findings.append(f"No accounts found across {len(selected)} checked sites (holehe).")
    return res


def _selected_callables(mods: dict):
    out = []
    for path, module in mods.items():
        short = path.split(".")[-1]
        if short in _ALLOW and hasattr(module, short):
            out.append((short, getattr(module, short)))
    return out


def _run(email: str, modules: list) -> list[dict]:
    import httpx
    import trio

    out: list[dict] = []

    async def _main():
        with trio.move_on_after(_TIMEOUT):
            async with httpx.AsyncClient(timeout=8) as client:
                async with trio.open_nursery() as nursery:
                    for mod in modules:
                        nursery.start_soon(_safe_mod, mod, email, client, out)

    async def _safe_mod(mod, email, client, out):
        try:
            await mod(email, client, out)
        except Exception:
            pass

    trio.run(_main)
    return out
