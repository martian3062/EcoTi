"""Email domain intelligence — MX / SPF / DMARC + disposable-domain check."""
from __future__ import annotations

import logging

from .base import EnrichResult

logger = logging.getLogger("ecoti.osint.dns")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "yopmail.com", "trashmail.com", "getnada.com", "sharklasers.com", "temp-mail.org",
    "throwawaymail.com", "fakeinbox.com", "maildrop.cc", "dispostable.com",
}


def _txt(domain: str) -> list[str]:
    import dns.resolver

    try:
        return [b"".join(r.strings).decode(errors="ignore") for r in dns.resolver.resolve(domain, "TXT")]
    except Exception:
        return []


def enrich(identifier: str, ctx: dict) -> EnrichResult:
    domain = identifier.split("@", 1)[1].lower()
    res = EnrichResult(sources=["DNS (MX/SPF/DMARC)"], attributes={"domain": domain})

    disposable = domain in DISPOSABLE_DOMAINS
    res.attributes["disposable"] = disposable
    if disposable:
        res.risk = 0.65
        res.findings.append(f"Disposable / throwaway email domain ({domain}).")

    try:
        import dns.resolver

        mx = []
        try:
            mx = [str(r.exchange).rstrip(".") for r in dns.resolver.resolve(domain, "MX")]
        except Exception:
            mx = []
        res.attributes["mx"] = mx[:5]
        if not mx:
            res.risk = max(res.risk, 0.5)
            res.findings.append("No MX record — domain can't receive mail (likely spoofed/typo).")

        txt = _txt(domain)
        has_spf = any(t.lower().startswith("v=spf1") for t in txt)
        has_dmarc = bool(_txt(f"_dmarc.{domain}"))
        res.attributes["spf"] = has_spf
        res.attributes["dmarc"] = has_dmarc
        if mx and not has_spf:
            res.risk = max(res.risk, 0.35)
            res.findings.append("No SPF record — sender can be spoofed.")
        if mx and has_spf and has_dmarc and not disposable:
            res.findings.append("Domain has valid MX + SPF + DMARC (well-configured).")
    except Exception as exc:  # pragma: no cover
        logger.warning("DNS enrich failed: %s", exc)
        res.findings.append("DNS lookup unavailable.")

    if res.risk >= 0.6:
        from core.events import A2AEvent

        res.event = A2AEvent(module="osint", signal="disposable_email", identifier=identifier,
                            confidence=round(res.risk, 2), payload={"domain": domain})
    return res
