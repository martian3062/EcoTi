"""Higher-accuracy phone intelligence.

Two layers, both graceful:
  * libphonenumber (``phonenumbers``) — offline, free, exact: validity, region,
    carrier, line-type (VOIP is a strong scam signal), E.164 normalisation.
  * IPQualityScore — real-time crowd-sourced phone reputation (fraud_score,
    recent_abuse, VOIP, active) when ``IPQS_API_KEY`` is set (free tier).
"""
from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger("ecoti.phone")

try:
    import phonenumbers
    from phonenumbers import PhoneNumberType, carrier, geocoder
    _HAS_PN = True
except Exception:  # pragma: no cover
    _HAS_PN = False

_TYPE = {}
if _HAS_PN:
    _TYPE = {
        PhoneNumberType.MOBILE: "mobile",
        PhoneNumberType.FIXED_LINE: "fixed_line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_or_mobile",
        PhoneNumberType.VOIP: "voip",
        PhoneNumberType.TOLL_FREE: "toll_free",
        PhoneNumberType.PREMIUM_RATE: "premium_rate",
        PhoneNumberType.SHARED_COST: "shared_cost",
        PhoneNumberType.UAN: "uan",
        PhoneNumberType.UNKNOWN: "unknown",
    }


def validate(raw: str, default_region: str = "IN") -> dict:
    """Offline validation via libphonenumber. Never raises."""
    if not _HAS_PN:
        return {"available": False}
    try:
        p = phonenumbers.parse(raw, default_region)
    except Exception:
        return {"available": True, "valid": False, "parse_error": True}
    try:
        valid = phonenumbers.is_valid_number(p)
        return {
            "available": True,
            "valid": valid,
            "possible": phonenumbers.is_possible_number(p),
            "e164": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164),
            "country_code": p.country_code,
            "region": geocoder.region_code_for_number(p) or "",
            "location": geocoder.description_for_number(p, "en") or "",
            "carrier": carrier.name_for_number(p, "en") or "",
            "line_type": _TYPE.get(phonenumbers.number_type(p), "unknown"),
        }
    except Exception as exc:  # pragma: no cover
        logger.warning("phonenumbers failed: %s", exc)
        return {"available": True, "valid": False}


def ipqs_lookup(e164: str, country: str = "IN") -> dict | None:
    """Real-time reputation via IPQualityScore (needs IPQS_API_KEY)."""
    key = getattr(settings, "IPQS_API_KEY", "")
    if not key:
        return None
    try:
        num = e164.lstrip("+")
        resp = requests.get(
            f"https://ipqualityscore.com/api/json/phone/{key}/{num}",
            params={"country[]": country},
            timeout=15,
        )
        resp.raise_for_status()
        d = resp.json()
        if not d.get("success", True):
            return None
        return {
            "fraud_score": d.get("fraud_score"),
            "recent_abuse": d.get("recent_abuse"),
            "voip": d.get("VOIP"),
            "risky": d.get("risky"),
            "active": d.get("active"),
            "spammer": d.get("spammer"),
            "line_type": d.get("line_type"),
            "carrier": d.get("carrier"),
        }
    except Exception as exc:  # pragma: no cover
        logger.warning("IPQS lookup failed: %s", exc)
        return None
