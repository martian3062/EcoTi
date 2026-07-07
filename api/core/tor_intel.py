"""Tor network traffic-pattern & anomaly detection.

Blends the "Tor Network Traffic Patterns and Anomaly Detection" work into EcoTi
as a dark-web intelligence layer — fraud gangs route C2, mule coordination and
cash-out through Tor. Uses the Tor Project's official **Onionoo** API (free, no
key) for live relay/exit data, then applies statistical + rule-based anomaly
detection:

  * BadExit-flagged relays (Tor-directory-flagged malicious exits)
  * bandwidth z-score outliers (possible traffic-shaping / sybil relays)
  * newly-seen high-bandwidth relays (sybil / injection indicator)
  * exit-node concentration by AS / country

Also answers "is this IP a Tor node/exit?" for the OSINT footprint.
(Onionoo replaces server-unfriendly local tools like Nyx; OONI Probe data is a
roadmap add for censorship/interference correlation.)
"""
from __future__ import annotations

import logging
import statistics
from datetime import datetime, timezone

import requests

logger = logging.getLogger("ecoti.tor")

ONIONOO = "https://onionoo.torproject.org"
_TIMEOUT = 25
_FIELDS = "nickname,fingerprint,country,country_name,as_name,flags,observed_bandwidth,consensus_weight,first_seen,last_seen,or_addresses,exit_addresses"


def _get(path: str, params: dict) -> dict:
    r = requests.get(f"{ONIONOO}/{path}", params=params, timeout=_TIMEOUT,
                     headers={"User-Agent": "EcoTi-TorIntel/1.0"})
    r.raise_for_status()
    return r.json()


def _days_since(ts: str) -> float:
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
    except Exception:
        return 9999.0


def summary() -> dict:
    """Live network snapshot: running exits, bad exits, top ASes."""
    try:
        exits = _get("details", {"flag": "Exit", "running": "true", "fields": "nickname,as_name,country"})
        bad = _get("details", {"flag": "BadExit", "fields": "nickname,as_name,country,last_seen"})
        exit_relays = exits.get("relays", [])
        # exit concentration by AS
        by_as: dict[str, int] = {}
        for r in exit_relays:
            by_as[r.get("as_name") or "unknown"] = by_as.get(r.get("as_name") or "unknown", 0) + 1
        top_as = sorted(by_as.items(), key=lambda kv: kv[1], reverse=True)[:6]
        return {
            "available": True,
            "published": exits.get("relays_published"),
            "running_exits": len(exit_relays),
            "bad_exits": len(bad.get("relays", [])),
            "top_exit_as": [{"as_name": a, "exits": n} for a, n in top_as],
        }
    except Exception as exc:
        logger.warning("Onionoo summary failed: %s", exc)
        return {"available": False, "error": str(exc)[:160]}


def _ml_scores(relays: list[dict]) -> dict[str, float]:
    """PyOD ECOD anomaly score (0..1) per relay over live features.
    Falls back to an empty dict (rule/z-score only) if PyOD/numpy unavailable."""
    try:
        import numpy as np
        from pyod.models.ecod import ECOD
    except Exception:
        return {}
    rows, fps = [], []
    for r in relays:
        bw = r.get("observed_bandwidth") or 0
        cw = r.get("consensus_weight") or 0
        age = _days_since(r.get("first_seen", ""))
        is_exit = 1.0 if "Exit" in r.get("flags", []) else 0.0
        rows.append([bw, cw, age, is_exit])
        fps.append(r.get("fingerprint") or r.get("nickname"))
    if len(rows) < 12:
        return {}
    X = np.array(rows, dtype=float)
    X = np.log1p(np.clip(X, 0, None))  # tame heavy-tailed bandwidth/weight
    try:
        clf = ECOD()
        clf.fit(X)
        raw = clf.decision_scores_
        lo, hi = float(raw.min()), float(raw.max())
        norm = (raw - lo) / (hi - lo) if hi > lo else raw * 0
        return {fp: round(float(s), 3) for fp, s in zip(fps, norm)}
    except Exception as exc:  # pragma: no cover
        logger.warning("PyOD scoring failed: %s", exc)
        return {}


def anomalies(limit: int = 80) -> dict:
    """Fetch high-weight relays + bad exits, score anomalies (rules + PyOD ML)."""
    try:
        top = _get("details", {"order": "-consensus_weight", "limit": limit,
                               "running": "true", "fields": _FIELDS}).get("relays", [])
        bad = _get("details", {"flag": "BadExit", "fields": _FIELDS}).get("relays", [])
    except Exception as exc:
        logger.warning("Onionoo anomalies failed: %s", exc)
        return {"available": False, "error": str(exc)[:160], "anomalies": []}

    bws = [r.get("observed_bandwidth", 0) for r in top if r.get("observed_bandwidth")]
    mean = statistics.mean(bws) if bws else 0
    stdev = statistics.pstdev(bws) if len(bws) > 1 else 0
    ml = _ml_scores(top)

    found: dict[str, dict] = {}

    def add(r: dict, reason: str, score: float):
        fp = r.get("fingerprint") or r.get("nickname")
        item = found.get(fp) or {
            "nickname": r.get("nickname"), "fingerprint": (r.get("fingerprint") or "")[:16],
            "country": r.get("country_name") or r.get("country"), "as_name": r.get("as_name"),
            "bandwidth_mbps": round((r.get("observed_bandwidth") or 0) / 125000, 1),
            "flags": r.get("flags", []), "is_exit": "Exit" in r.get("flags", []),
            "age_days": round(_days_since(r.get("first_seen", "")), 1),
            "ml_score": ml.get(fp), "reasons": [], "score": 0.0,
        }
        item["reasons"].append(reason)
        item["score"] = round(min(0.99, max(item["score"], score)), 2)
        found[fp] = item

    # 1) BadExit-flagged (directory-flagged malicious/misconfigured exits)
    for r in bad:
        add(r, "Flagged BadExit by the Tor directory (malicious/misconfigured exit).", 0.9)

    # 2) bandwidth z-score outliers among top relays
    for r in top:
        bw = r.get("observed_bandwidth", 0)
        if stdev and bw:
            z = (bw - mean) / stdev
            if z >= 3.0:
                add(r, f"Bandwidth outlier (z={z:.1f}) — possible traffic-shaping / sybil.", min(0.85, 0.5 + z / 12))
        # 3) newly-seen high-bandwidth relay (sybil / injection indicator)
        age = _days_since(r.get("first_seen", ""))
        if age <= 30 and bw >= (mean or 0) and "Exit" in r.get("flags", []):
            add(r, f"New exit ({age:.0f}d old) already high-bandwidth — sybil/injection risk.", 0.7)
        # 4) exit without Fast/Stable (unusual for a high-weight exit)
        if "Exit" in r.get("flags", []) and "Stable" not in r.get("flags", []):
            add(r, "High-weight exit lacking Stable flag — unstable/short-lived exit.", 0.45)
        # 5) PyOD ECOD multivariate anomaly (bandwidth × weight × age × exit)
        fp = r.get("fingerprint") or r.get("nickname")
        mlv = ml.get(fp)
        if mlv is not None and mlv >= 0.85:
            add(r, f"PyOD ECOD multivariate anomaly (ml={mlv:.2f}) across bandwidth/weight/age.", mlv)

    # Blend: nudge rule scores up when the ML model strongly agrees.
    for fp, item in found.items():
        mlv = ml.get(fp)
        if mlv is not None:
            item["score"] = round(min(0.99, item["score"] + 0.1 * max(0.0, mlv - 0.5)), 2)

    items = sorted(found.values(), key=lambda x: x["score"], reverse=True)
    return {
        "available": True,
        "sampled_relays": len(top),
        "mean_bandwidth_mbps": round(mean / 125000, 1) if mean else 0,
        "ml_engine": "pyod-ecod" if ml else "rules-only",
        "anomalies": items[:40],
    }


def check_ip(ip: str) -> dict:
    """Is this IP a Tor relay/exit? Live Onionoo lookup."""
    try:
        data = _get("details", {"search": ip, "fields": _FIELDS})
    except Exception as exc:
        return {"available": False, "error": str(exc)[:160]}
    relays = data.get("relays", [])
    if not relays:
        return {"available": True, "is_tor": False, "ip": ip}
    r = relays[0]
    flags = r.get("flags", [])
    return {
        "available": True,
        "is_tor": True,
        "is_exit": "Exit" in flags,
        "bad_exit": "BadExit" in flags,
        "ip": ip,
        "nickname": r.get("nickname"),
        "country": r.get("country_name") or r.get("country"),
        "as_name": r.get("as_name"),
        "flags": flags,
        "bandwidth_mbps": round((r.get("observed_bandwidth") or 0) / 125000, 1),
        "first_seen": r.get("first_seen"),
        "matches": len(relays),
    }
