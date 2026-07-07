"""Geospatial Crime-Pattern Command Centre swarm.

Sub-agents: hotspot_mapper · patrol_prioritiser · inter_district_alerter.
P0 returns a deterministic set of hotspots + patrol priorities for the map.
"""
from __future__ import annotations

import hashlib
import time

from core.events import A2AEvent, Module
from core.swarm import BaseSwarm, SubAgent

# Nationwide complaint/seizure hotspots — cyber-fraud hubs across India
# (NCRB aggregates + Jamtara/Mewat/Bharatpur belt + metros, synthetic stand-in).
_HOTSPOTS = [
    {"district": "Jamtara", "state": "Jharkhand", "lat": 23.9629, "lng": 86.8020, "base": 0.96},
    {"district": "Mewat (Nuh)", "state": "Haryana", "lat": 28.1080, "lng": 77.0010, "base": 0.92},
    {"district": "Bharatpur", "state": "Rajasthan", "lat": 27.2173, "lng": 77.4901, "base": 0.88},
    {"district": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873, "base": 0.86},
    {"district": "Alwar", "state": "Rajasthan", "lat": 27.5530, "lng": 76.6346, "base": 0.80},
    {"district": "Deoghar", "state": "Jharkhand", "lat": 24.4823, "lng": 86.6968, "base": 0.78},
    {"district": "Gurugram", "state": "Haryana", "lat": 28.4595, "lng": 77.0266, "base": 0.76},
    {"district": "Delhi (Outer)", "state": "Delhi", "lat": 28.7041, "lng": 77.1025, "base": 0.82},
    {"district": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "base": 0.74},
    {"district": "Nalanda", "state": "Bihar", "lat": 25.1372, "lng": 85.4436, "base": 0.70},
    {"district": "Nawada", "state": "Bihar", "lat": 24.8880, "lng": 85.5435, "base": 0.72},
    {"district": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639, "base": 0.68},
    {"district": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867, "base": 0.66},
    {"district": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "base": 0.71},
    {"district": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707, "base": 0.60},
    {"district": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714, "base": 0.63},
    {"district": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462, "base": 0.65},
    {"district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567, "base": 0.58},
    {"district": "Patna", "state": "Bihar", "lat": 25.5941, "lng": 85.1376, "base": 0.62},
    {"district": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lng": 77.4126, "base": 0.55},
]


def _live_intensity(base: float, key: str, bucket: int) -> float:
    """Deterministic-per-minute variation so the map feels live/real-time."""
    h = hashlib.sha256(f"{key}:{bucket}".encode()).hexdigest()
    swing = (int(h[:4], 16) / 0xFFFF - 0.5) * 0.16  # ±0.08
    return round(max(0.15, min(0.99, base + swing)), 2)


def _hotspot_mapper(state: dict) -> dict:
    bucket = int(time.time() // 60)  # changes each minute
    focus = state.get("districts")
    hotspots = []
    for h in _HOTSPOTS:
        if focus and h["district"] not in focus:
            continue
        intensity = _live_intensity(h["base"], h["district"], bucket)
        hotspots.append({
            "district": h["district"],
            "state": h["state"],
            "lat": h["lat"],
            "lng": h["lng"],
            "intensity": intensity,
            "complaints": int(30 + intensity * 180),
        })
    return {"hotspots": hotspots or []}


def _patrol_prioritiser(state: dict) -> dict:
    ranked = sorted(state["hotspots"], key=lambda h: h["intensity"], reverse=True)
    return {"patrol_priority": [{"district": h["district"], "rank": i + 1}
                                for i, h in enumerate(ranked)]}


def _inter_district_alerter(state: dict) -> dict:
    hot = [h["district"] for h in state["hotspots"] if h["intensity"] >= 0.7]
    return {"inter_district_alert": len(hot) >= 2, "alert_districts": hot}


swarm = BaseSwarm(
    name="geo_command",
    sub_agents=[
        SubAgent("hotspot_mapper", _hotspot_mapper),
        SubAgent("patrol_prioritiser", _patrol_prioritiser),
        SubAgent("inter_district_alerter", _inter_district_alerter),
    ],
)


def run(inputs: dict) -> dict:
    state = swarm.run(inputs)
    top = max(state["hotspots"], key=lambda h: h["intensity"])
    state["event"] = A2AEvent(
        module=Module.GEO_COMMAND.value,
        signal="geo_hotspot",
        identifier=inputs.get("identifier"),
        confidence=top["intensity"],
        payload={
            "hotspots": state["hotspots"],
            "patrol_priority": state["patrol_priority"],
            "inter_district_alert": state["inter_district_alert"],
            "alert_districts": state["alert_districts"],
        },
    )
    return state
