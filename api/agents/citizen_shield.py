"""Citizen Fraud Shield swarm.

Sub-agents: risk_assessor, guided_reporter, advisory_generator. The citizen path
defaults to edge/offline inference, using the same script bank as Scam-Call so
the P1 demo can prove consistent detection across call transcripts and forwarded
messages.
"""
from __future__ import annotations

from core import llm
from core.events import A2AEvent, Module
from core.script_bank import all_markers, match_script
from core.swarm import BaseSwarm, SubAgent

LANGS = ["en", "hi", "ta", "kn", "te", "ml", "mr", "gu", "bn", "pa", "or", "as"]

_SCAM_MARKERS = all_markers() + ["ed officer", "lottery", "blocked"]

# Compact 12-language demo advisories. These are transliterated so they remain
# ASCII-safe in terminals while still being language-specific for the demo.
_VERDICT_TEXT = {
    "scam": {
        "en": "FRAUD. No agency arrests over video. Do not pay. Report on 1930.",
        "hi": "Dhokha. Koi agency video par arrest nahi karti. Paisa na dein. 1930 par report karein.",
        "ta": "Mosadi. Video-vil arrest illai. Panam anuppatheergal. 1930-il report seyyungal.",
        "kn": "Vanchane. Video arrest illa. Hana kaluhisabedi. 1930 ge report madi.",
        "te": "Mosam. Video lo arrest cheyaru. Dabbu pampakandi. 1930 ki report cheyandi.",
        "ml": "Thattippu. Video arrest illa. Panam ayakkaruthu. 1930-il report cheyyuka.",
        "mr": "Fasavanuk. Video var arrest hot nahi. Paise deu naka. 1930 var report kara.",
        "gu": "Thagayi. Video par arrest thati nathi. Paisa na aapo. 1930 par report karo.",
        "bn": "Protarona. Video call-e arrest hoy na. Taka deben na. 1930-e report korun.",
        "pa": "Dhokha. Video te arrest nahi hundi. Paise na bhejo. 1930 te report karo.",
        "or": "Thakei. Video re arrest hue nahi. Tanka pathantu nahi. 1930 re report karantu.",
        "as": "Protarona. Video call-t arrest nokore. Toka nidiyok. 1930-t report korok.",
    },
    "suspicious": {
        "en": "Suspicious. Do not share OTP/KYC. Verify on the official number.",
        "hi": "Sandehjanak. OTP/KYC share na karein. Official number par verify karein.",
        "ta": "Sandhegam. OTP/KYC pagiratheergal. Official number-il verify seyyungal.",
        "kn": "Anumana. OTP/KYC hanchabedi. Official number nalli verify madi.",
        "te": "Anumanam. OTP/KYC share cheyakandi. Official number lo verify cheyandi.",
        "ml": "Samshayam. OTP/KYC share cheyyaruthu. Official number-il verify cheyyuka.",
        "mr": "Sanshayaspad. OTP/KYC share karu naka. Official number var verify kara.",
        "gu": "Shankaspad. OTP/KYC share na karo. Official number par verify karo.",
        "bn": "Sondehojonok. OTP/KYC share korben na. Official number-e verify korun.",
        "pa": "Shakki. OTP/KYC share na karo. Official number te verify karo.",
        "or": "Sandehajanaka. OTP/KYC share karantu nahi. Official number re verify karantu.",
        "as": "Sondehjanok. OTP/KYC share nokoribo. Official number-t verify korok.",
    },
    "safe": {
        "en": "Looks safe. Stay alert and never share OTP.",
        "hi": "Safe lagta hai. Satark rahen aur OTP kabhi share na karein.",
        "ta": "Safe pola therigirathu. Echarikkaiyaga irungal; OTP pagiratheergal.",
        "kn": "Surakshita anisutte. Echarike irali; OTP hanchabedi.",
        "te": "Safe ga undi. Jagrattaga undandi; OTP share cheyakandi.",
        "ml": "Safe pole thonnunnu. Jagratha; OTP share cheyyaruthu.",
        "mr": "Surakshit disate. Satark raha; OTP share karu naka.",
        "gu": "Safe lage chhe. Savdhan raho; OTP share na karo.",
        "bn": "Nirapod mone hocche. Sotorko thakun; OTP share korben na.",
        "pa": "Safe lagda hai. Savdhan raho; OTP share na karo.",
        "or": "Safe laguchi. Satarka ruhantu; OTP share karantu nahi.",
        "as": "Safe buli lage. Sotorko thakok; OTP share nokoribo.",
    },
}


def _risk_assessor(state: dict) -> dict:
    text = (state.get("message") or "").lower()
    match = match_script(text)
    hits = [marker for marker in _SCAM_MARKERS if marker in text]
    marker_score = min(0.97, len(hits) / 3.0)
    score = max(marker_score, match["score"])
    verdict = "scam" if score >= 0.6 else "suspicious" if score >= 0.3 else "safe"

    # The router keeps this local when edge=True. In stub mode it remains fully
    # deterministic, so demos do not need a model server.
    llm.complete(f"classify fraud risk: {text[:200]}", force_edge=state.get("edge", True))
    return {
        "verdict": verdict,
        "confidence": round(score, 2),
        "matched_markers": sorted(set(hits + match["matched_markers"])),
        "matched_script": match,
        "edge_runtime": llm.runtime_info(force_edge=state.get("edge", True)),
    }


def _guided_reporter(state: dict) -> dict:
    if state["verdict"] == "safe":
        return {"report_draft": None}
    return {
        "report_draft": {
            "portal": "I4C / cybercrime.gov.in / 1930",
            "category": "Financial Fraud - Digital Arrest"
            if state.get("matched_script", {}).get("pattern_id") == "digital_arrest_v1"
            else "Financial Fraud",
            "identifier": state.get("identifier"),
            "summary": (state.get("message") or "")[:280],
            "steps": [
                "Do not transfer any money.",
                "Disconnect the call immediately.",
                "Call the 1930 cyber helpline.",
                "File a complaint at cybercrime.gov.in with this draft.",
            ],
        }
    }


def _advisory_generator(state: dict) -> dict:
    lang = state.get("lang", "en") if state.get("lang") in LANGS else "en"
    bucket = _VERDICT_TEXT.get(state["verdict"], {})
    text = bucket.get(lang) or bucket.get("en", "")
    return {"advisory": text, "lang": lang}


swarm = BaseSwarm(
    name="citizen_shield",
    sub_agents=[
        SubAgent("risk_assessor", _risk_assessor),
        SubAgent("guided_reporter", _guided_reporter),
        SubAgent("advisory_generator", _advisory_generator),
    ],
)


def run(inputs: dict) -> dict:
    inputs.setdefault("edge", True)  # citizen tool defaults to on-device
    state = swarm.run(inputs)
    state["event"] = A2AEvent(
        module=Module.CITIZEN_SHIELD.value,
        signal="shield_verdict",
        identifier=inputs.get("identifier"),
        confidence=state.get("confidence", 0.0),
        route="edge" if inputs.get("edge", True) else "cloud",
        payload={
            "verdict": state.get("verdict"),
            "advisory": state.get("advisory"),
            "lang": state.get("lang"),
            "report_draft": state.get("report_draft"),
            "matched_script": state.get("matched_script"),
            "edge_runtime": state.get("edge_runtime"),
        },
    )
    return state
