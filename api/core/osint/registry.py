"""OSINT enricher registry — concurrent, self-healing aggregation + fusion + cache."""
from __future__ import annotations

import concurrent.futures
import logging

from core import bus, llm

from . import cache
from .base import EnrichResult
from . import dns_email, gravatar, hibp, holehe_enricher, ipintel, phone, upi, username

logger = logging.getLogger("ecoti.osint")

# (name, kinds, fn). Order is display-priority for findings.
ENRICHERS: list[tuple[str, set, object]] = [
    ("phone", {"phone"}, phone.enrich),
    ("upi", {"upi"}, upi.enrich),
    ("hibp", {"email"}, hibp.enrich),
    ("holehe", {"email"}, holehe_enricher.enrich),
    ("dns", {"email"}, dns_email.enrich),
    ("gravatar", {"email"}, gravatar.enrich),
    ("ipintel", {"ip"}, ipintel.enrich),
    ("username", {"username"}, username.enrich),
]

_TIMEOUT = 30


def _safe(name, fn, identifier, ctx) -> EnrichResult | None:
    """Run an enricher; a failure degrades to None (self-healing)."""
    try:
        return fn(identifier, ctx)
    except Exception as exc:  # pragma: no cover
        logger.warning("enricher %s failed: %s", name, exc)
        return None


def aggregate(identifier: str, kind: str, lang: str = "en") -> dict:
    cached = cache.get(kind, identifier)
    if cached is not None:
        return {**cached, "cached": True}

    ctx = {"lang": lang, "kind": kind}
    applicable = [(n, fn) for (n, ks, fn) in ENRICHERS if kind in ks]
    results: list[tuple[str, EnrichResult]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_safe, n, fn, identifier, ctx): n for (n, fn) in applicable}
        try:
            for fut in concurrent.futures.as_completed(futs, timeout=_TIMEOUT):
                r = fut.result()
                if r:
                    results.append((futs[fut], r))
        except concurrent.futures.TimeoutError:
            logger.warning("some enrichers timed out for %s", identifier)

    # fuse
    risk = max([r.risk for _, r in results], default=0.0)
    findings: list[str] = []
    attributes: dict = {}
    sources: list[str] = []
    nodes: list[dict] = [{"id": identifier, "label": identifier, "type": kind, "risk": round(risk, 2)}]
    edges: list[dict] = []
    events = []
    for _, r in sorted(results, key=lambda x: x[1].risk, reverse=True):
        findings += r.findings
        attributes.update(r.attributes)
        for s in r.sources:
            if s not in sources:
                sources.append(s)
        nodes += r.nodes
        edges += r.edges
        if r.event is not None:
            events.append(r.event)

    verdict = "scam" if risk >= 0.6 else "suspicious" if risk >= 0.3 else "safe" if kind in {"phone", "ip", "upi"} else "unknown"
    fp = {
        "identifier": identifier,
        "kind": kind,
        "risk_score": round(risk, 2),
        "verdict": verdict,
        "findings": findings,
        "attributes": attributes,
        "sources": sources,
        "graph": {"nodes": nodes, "edges": edges},
        "lang": lang,
        "cached": False,
    }
    fp["osint_summary"] = _summary(identifier, fp, lang)

    # fusion + live feed (best-effort)
    try:
        from orchestrator import correlator

        for ev in events:
            correlator.ingest(ev)
    except Exception as exc:  # pragma: no cover
        logger.warning("OSINT fusion emit failed: %s", exc)
    try:
        bus.publish_toast(
            f"OSINT · {kind} · {identifier} → {verdict} ({fp['risk_score']})",
            level="info", extra={"osint": True, "kind": kind},
        )
    except Exception:
        pass

    cache.set(kind, identifier, fp)
    return fp


def _summary(identifier: str, fp: dict, lang: str) -> str:
    prompt = (
        f"OSINT digital-footprint request for {fp['kind']} identifier '{identifier}'. "
        f"Findings: {'; '.join(fp['findings'][:8])}. Risk score {fp['risk_score']}. "
        f"In 2-3 sentences, give an investigator-style summary and the most useful next step."
    )
    text = llm.complete(prompt, system="You are EcoTi's OSINT analyst for financial-fraud triage. Be factual and concise.")
    if not text or text.startswith("[stub-verdict]"):
        return f"Footprint for {identifier} ({fp['kind']}): " + " ".join(fp["findings"][:3])
    if lang not in {"en", "en-IN"}:
        text = llm.translate(text, lang)
    return text.strip()
