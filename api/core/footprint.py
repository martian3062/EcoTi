"""Digital footprint / OSINT aggregator.

Given any identifier (phone · email · UPI handle · username/domain), compose a
broader picture from all live signals EcoTi can reach — no scraping of ToS-
protected social sites; only deterministic, defensible checks:

  * phone  → libphonenumber + IPQS reputation + fraud-graph linkage + history
  * email  → syntax/domain validity, disposable-domain check, Gravatar presence
  * upi    → handle/bank parse + linkage against the fraud graph
  * other  → treated as a username/handle for the LLM OSINT summary

Every lookup is also pushed to the command-centre live feed (OSINT stream), and
an LLM synthesises an investigator-style summary + suggested next OSINT steps.
"""
from __future__ import annotations

import hashlib
import re

import requests

from . import bus, llm, phone_reputation

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UPI_RE = re.compile(r"^[\w.\-]{2,}@[a-zA-Z]{2,}$")  # handle@bank (no dot after @)
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,}$")
IPV4_RE = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "yopmail.com", "trashmail.com", "getnada.com", "sharklasers.com",
}
UPI_BANKS = {
    "okhdfcbank": "HDFC Bank", "oksbi": "State Bank of India", "okaxis": "Axis Bank",
    "okicici": "ICICI Bank", "ybl": "PhonePe (Yes Bank)", "paytm": "Paytm",
    "apl": "Amazon Pay", "ibl": "PhonePe (IDFC)", "axl": "Axis / Google Pay",
}


def classify(identifier: str) -> str:
    s = (identifier or "").strip()
    m = IPV4_RE.match(s)
    if m and all(0 <= int(g) <= 255 for g in m.groups()):
        return "ip"
    if EMAIL_RE.match(s):
        return "email"
    if PHONE_RE.match(s) and sum(c.isdigit() for c in s) >= 7 and "@" not in s:
        return "phone"
    if UPI_RE.match(s):
        return "upi"
    return "username"


def _ip_footprint(identifier: str) -> dict:
    from . import tor_intel

    tor = tor_intel.check_ip(identifier)
    findings: list[str] = []
    risk = 0.0
    if tor.get("is_tor"):
        risk = 0.75 if tor.get("is_exit") else 0.5
        findings.append(
            f"IP is a Tor {'EXIT' if tor.get('is_exit') else 'relay'} node "
            f"({tor.get('nickname')}, {tor.get('country')}, {tor.get('as_name')})."
        )
        if tor.get("bad_exit"):
            risk = 0.9
            findings.append("Flagged as a BadExit — malicious/misconfigured Tor exit.")
        findings.append("Traffic from Tor exits is anonymised — treat linked activity as high-risk.")
    elif tor.get("available"):
        findings.append("Not a known Tor relay/exit node.")
    else:
        findings.append("Tor lookup unavailable right now.")
    return {
        "kind": "ip",
        "risk_score": round(risk, 2),
        "verdict": "scam" if risk >= 0.6 else "suspicious" if risk >= 0.3 else "safe",
        "attributes": {
            "is_tor": tor.get("is_tor"), "is_exit": tor.get("is_exit"),
            "bad_exit": tor.get("bad_exit"), "country": tor.get("country"),
            "as_name": tor.get("as_name"), "flags": tor.get("flags"),
        },
        "findings": findings,
        "sources": ["Tor Onionoo"],
        "detail": {"tor": tor},
    }


def _gravatar(email: str) -> dict:
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    out = {"hash": h, "exists": False, "profile_url": f"https://gravatar.com/{h}"}
    try:
        r = requests.get(f"https://www.gravatar.com/avatar/{h}?d=404", timeout=8)
        out["exists"] = r.status_code == 200
        if out["exists"]:
            out["avatar_url"] = f"https://www.gravatar.com/avatar/{h}"
    except Exception:
        pass
    return out


def _phone_footprint(identifier: str, lang: str) -> dict:
    from .number_intel import check_number

    chk = check_number(identifier, lang)
    sources = ["libphonenumber", "EcoTi fraud-graph", "reported history", "community reports"]
    if chk.get("reputation", {}).get("available"):
        sources.append("IPQualityScore")
    return {
        "kind": "phone",
        "risk_score": chk["risk_score"],
        "verdict": chk["verdict"],
        "attributes": {
            "line_type": chk["validation"].get("line_type"),
            "carrier": chk["validation"].get("carrier"),
            "region": chk["validation"].get("region"),
            "valid": chk["validation"].get("valid"),
            "mule_cluster": chk["graph"].get("cluster_size"),
            "districts": chk["graph"].get("districts"),
        },
        "findings": chk["reasons"],
        "sources": sources,
        "detail": chk,
    }


def _email_footprint(identifier: str) -> dict:
    domain = identifier.split("@", 1)[1].lower()
    disposable = domain in DISPOSABLE_DOMAINS
    grav = _gravatar(identifier)
    findings = []
    risk = 0.0
    if disposable:
        risk = 0.7
        findings.append(f"Disposable / throwaway email domain ({domain}).")
    if grav["exists"]:
        findings.append("Public Gravatar profile exists (identity has some web presence).")
    else:
        findings.append("No public Gravatar profile found.")
    findings.append(f"Domain: {domain}. Verify MX/SPF before trusting sender.")
    return {
        "kind": "email",
        "risk_score": round(risk, 2),
        "verdict": "suspicious" if disposable else "unknown",
        "attributes": {"domain": domain, "disposable": disposable,
                       "gravatar": grav["exists"], "gravatar_profile": grav["profile_url"]},
        "findings": findings,
        "sources": ["syntax/domain check", "disposable-domain list", "Gravatar"],
        "detail": {"gravatar": grav},
    }


def _upi_footprint(identifier: str, lang: str) -> dict:
    handle, bank_code = identifier.split("@", 1)
    bank = UPI_BANKS.get(bank_code.lower(), f"Unknown PSP ({bank_code})")
    # A UPI handle often embeds a phone number — check that too.
    phone_like = re.sub(r"\D", "", handle)
    findings = [f"UPI handle on {bank}."]
    risk = 0.0
    detail = {}
    if len(phone_like) == 10:
        from .number_intel import check_number

        chk = check_number("+91" + phone_like, lang)
        risk = chk["risk_score"]
        findings.append(f"Embedded number +91{phone_like}: {chk['verdict']} ({chk['risk_score']}).")
        findings += chk["reasons"][:2]
        detail["number"] = chk
    return {
        "kind": "upi",
        "risk_score": round(risk, 2),
        "verdict": "scam" if risk >= 0.6 else "suspicious" if risk >= 0.3 else "unknown",
        "attributes": {"handle": handle, "bank": bank, "embedded_number": phone_like or None},
        "findings": findings,
        "sources": ["UPI PSP map", "EcoTi fraud-graph"],
        "detail": detail,
    }


def _username_footprint(identifier: str) -> dict:
    from . import username_osint

    scan = username_osint.scan(identifier)
    hits = scan.get("hits", [])
    findings = []
    if not scan.get("valid"):
        findings.append("Not a valid username format.")
    elif hits:
        sites = ", ".join(h["site"] for h in hits[:10])
        findings.append(f"Public profile found on {len(hits)} platform(s): {sites}.")
        findings.append("Cross-reference these profiles to verify identity / linked accounts.")
    else:
        findings.append(f"No public profile found across {scan.get('checked', 0)} checked platforms.")
    return {
        "kind": "username",
        # presence isn't itself 'risk'; keep it informational (unknown verdict)
        "risk_score": 0.0,
        "verdict": "unknown",
        "attributes": {
            "handle": identifier,
            "profiles_found": len(hits),
            "platforms_checked": scan.get("checked", 0),
        },
        "findings": findings,
        "sources": ["WhatsMyName-style username scan"],
        "detail": {"profiles": hits},
    }


def build_footprint(identifier: str, lang: str = "en") -> dict:
    kind = classify(identifier)
    if kind == "phone":
        fp = _phone_footprint(identifier, lang)
    elif kind == "email":
        fp = _email_footprint(identifier)
    elif kind == "upi":
        fp = _upi_footprint(identifier, lang)
    elif kind == "ip":
        fp = _ip_footprint(identifier)
    else:
        fp = _username_footprint(identifier)

    fp["identifier"] = identifier
    fp["osint_summary"] = _summary(identifier, fp, lang)

    # push to the live OSINT feed on the command centre
    try:
        bus.publish_toast(
            f"OSINT lookup · {kind} · {identifier} → {fp['verdict']} ({fp['risk_score']})",
            level="info", extra={"osint": True, "kind": kind},
        )
    except Exception:
        pass
    return fp


def _summary(identifier: str, fp: dict, lang: str) -> str:
    prompt = (
        f"OSINT digital-footprint request for {fp['kind']} identifier '{identifier}'. "
        f"Findings: {'; '.join(fp['findings'])}. Risk score {fp['risk_score']}. "
        f"In 2-3 sentences, give an investigator-style summary of the digital footprint "
        f"and the most useful next verification step for a citizen or analyst."
    )
    text = llm.complete(prompt, system="You are EcoTi's OSINT analyst for financial-fraud triage. Be factual and concise.")
    if not text or text.startswith("[stub-verdict]"):
        return (f"Footprint for {identifier} ({fp['kind']}): "
                + " ".join(fp["findings"][:3]))
    if lang not in {"en", "en-IN"}:
        text = llm.translate(text, lang)
    return text.strip()
