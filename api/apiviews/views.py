"""DRF endpoints — per-agent + orchestrator fusion + event history.

Every agent runs through the self-healing planner (``orchestrator.planner.run_agent``)
and emits its A2A event into the correlator, which may fire a fused TrustRisk.
"""
from __future__ import annotations

from agents import AGENT_REGISTRY
from core.models import AgentHealth, EvidencePacket, FusedTrustRiskRecord, TrustEvent
from drf_spectacular.utils import extend_schema
from orchestrator import correlator, planner
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import (
    AgentRequestSerializer,
    AgentStatusSerializer,
    CounterfeitRequestSerializer,
    EventsHistorySerializer,
    EvidencePacketSerializer,
    GenericAgentResponseSerializer,
    GeoHotspotRequestSerializer,
    P1CoreDemoRequestSerializer,
    P1CoreDemoResponseSerializer,
    ScamCallRequestSerializer,
    ShieldRequestSerializer,
)


@extend_schema(tags=["system"])
@api_view(["GET"])
def providers_health(request):
    """Live reachability of the configured real AI providers (Groq/Kimi/Sarvam/HF/Firecrawl)."""
    from core import llm

    return Response(llm.health())


@extend_schema(tags=["tor"])
@api_view(["GET"])
def tor_summary(request):
    """Live Tor network snapshot (running exits, bad exits, AS concentration)."""
    from core import tor_intel

    return Response(tor_intel.summary())


@extend_schema(tags=["tor"])
@api_view(["GET"])
def tor_anomalies(request):
    """Tor relay anomaly detection over live Onionoo data."""
    from core import tor_intel

    return Response(tor_intel.anomalies(int(request.query_params.get("limit", 80))))


@extend_schema(tags=["tor"])
@api_view(["POST"])
def tor_check_ip(request):
    """Is this IP a Tor relay/exit node?"""
    from core import tor_intel

    ip = ((request.data or {}).get("ip") or "").strip()
    if not ip:
        return Response({"error": "ip required"}, status=400)
    return Response(tor_intel.check_ip(ip))


@extend_schema(tags=["system"])
@api_view(["GET"])
def news_feed(request):
    """Live fraud/cyber news headlines (Google News RSS) for the ticker."""
    from core.news import headlines

    return Response({"items": headlines(int(request.query_params.get("limit", 24)))})


@extend_schema(tags=["system"])
@api_view(["GET"])
def news_anchor(request):
    """AI news-anchor bulletin (LLM summary of the top fraud headlines)."""
    from core.news import anchor_bulletin

    return Response(anchor_bulletin())


@extend_schema(tags=["system"])
@api_view(["POST"])
def tts_speak(request):
    """Human TTS (Sarvam Bulbul) → base64 WAV for the AI anchor."""
    from core import llm

    data = request.data or {}
    text = (data.get("text") or "").strip()
    if not text:
        return Response({"error": "text required"}, status=400)
    audio = llm.tts(text, lang=data.get("lang", "en"), speaker=data.get("speaker", "anushka"))
    return Response({"audio_b64": audio, "format": "wav"})


@extend_schema(tags=["citizen"])
@api_view(["POST"])
def footprint(request):
    """Digital footprint / OSINT aggregation for a phone / email / UPI / username."""
    from core.footprint import build_footprint

    data = request.data or {}
    identifier = (data.get("identifier") or "").strip()
    if not identifier:
        return Response({"error": "identifier required"}, status=400)
    return Response(build_footprint(identifier, lang=data.get("lang", "en")))


@extend_schema(tags=["citizen"])
@api_view(["POST"])
def report_fraud(request):
    """Submit a citizen fraud report. The reported number joins the community
    watchlist and immediately raises the risk of future number checks."""
    from core.models import FraudReport
    from core.number_intel import check_number, normalize

    data = request.data or {}
    raw = (data.get("number") or "").strip()
    if not raw:
        return Response({"error": "number required"}, status=400)
    number = normalize(raw)
    report = FraudReport.objects.create(
        number=number,
        category=data.get("category", "other"),
        description=(data.get("description") or "")[:2000],
        amount_lost=data.get("amount_lost") or None,
        reporter_contact=(data.get("reporter_contact") or "")[:128],
        channel=data.get("channel", "web"),
    )
    total = FraudReport.objects.filter(number=number).count()
    return Response({
        "ok": True,
        "id": report.id,
        "number": number,
        "reports_for_number": total,
        "updated_check": check_number(number, lang=data.get("lang", "en")),
    })


@extend_schema(tags=["citizen"])
@api_view(["GET"])
def report_recent(request):
    """Recent fraud reports (contact redacted) + per-category counts."""
    from django.db.models import Count

    from core.models import FraudReport

    rows = FraudReport.objects.all()[:30]
    by_cat = list(FraudReport.objects.values("category").annotate(n=Count("id")).order_by("-n"))
    return Response({
        "total": FraudReport.objects.count(),
        "by_category": by_cat,
        "recent": [
            {
                "number": r.number, "category": r.category,
                "description": r.description[:160], "amount_lost": str(r.amount_lost or ""),
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    })


@extend_schema(tags=["citizen"])
@api_view(["POST"])
def number_check(request):
    """Check whether a mobile number is a scam: fraud-graph linkage + reported
    history + number heuristics + a localised LLM advisory."""
    from core.number_intel import check_number

    data = request.data or {}
    number = (data.get("number") or "").strip()
    if not number:
        return Response({"error": "number required"}, status=400)
    return Response(check_number(number, lang=data.get("lang", "en")))


@extend_schema(tags=["rag"])
@api_view(["POST"])
def rag_ask(request):
    """Advisory copilot: answer a fraud question grounded in the ingested corpus."""
    from rag.retrieve import ask

    question = (request.data or {}).get("question", "").strip()
    if not question:
        return Response({"error": "question required"}, status=400)
    return Response(ask(question))


@extend_schema(tags=["rag"])
@api_view(["GET"])
def rag_sources(request):
    """List the ingested advisory sources."""
    from rag.models import AdvisorySource

    return Response([
        {"authority": s.authority, "title": s.title, "url": s.url,
         "origin": s.origin, "chunks": s.chunks.count()}
        for s in AdvisorySource.objects.all()
    ])


def _run_and_correlate(agent: str, payload: dict) -> dict:
    """Run an agent via the planner, push its event to the correlator, fuse."""
    state = planner.run_agent(agent, payload)
    event = state.get("event")
    fused = None
    if event is not None:
        fused = correlator.ingest(event)
    out = {k: v for k, v in state.items() if not k.startswith("_") and k != "event"}
    out["route"] = state.get("_route", "primary")
    if state.get("_fallback_used"):
        out["fallback_used"] = state["_fallback_used"]
    if fused is not None:
        out["fused_trust_risk"] = fused.model_dump_jsonable()
    if event is not None:
        out["event"] = event.model_dump_jsonable()
    return out


def _validated(serializer_cls, data) -> dict:
    serializer = serializer_cls(data=data)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


@extend_schema(
    request=ScamCallRequestSerializer,
    responses=GenericAgentResponseSerializer,
    tags=["agents"],
)
@api_view(["POST"])
def scam_call_analyze(request):
    return Response(_run_and_correlate("scam_call", _validated(ScamCallRequestSerializer, request.data)))


@extend_schema(
    request=CounterfeitRequestSerializer,
    responses=GenericAgentResponseSerializer,
    tags=["agents"],
)
@api_view(["POST"])
def counterfeit_verify(request):
    return Response(
        _run_and_correlate(
            "counterfeit_vision",
            _validated(CounterfeitRequestSerializer, request.data),
        )
    )


@extend_schema(
    request=AgentRequestSerializer,
    responses=GenericAgentResponseSerializer,
    tags=["agents"],
)
@api_view(["POST"])
def fraud_graph_score(request):
    return Response(_run_and_correlate("fraud_graph", _validated(AgentRequestSerializer, request.data)))


@extend_schema(
    request=ShieldRequestSerializer,
    responses=GenericAgentResponseSerializer,
    tags=["agents"],
)
@api_view(["POST"])
def shield_assess(request):
    return Response(_run_and_correlate("citizen_shield", _validated(ShieldRequestSerializer, request.data)))


@extend_schema(
    request=P1CoreDemoRequestSerializer,
    responses=P1CoreDemoResponseSerializer,
    tags=["demos"],
)
@api_view(["POST"])
def p1_core_demo(request):
    """Run the P1 spine: scam transcript -> local Shield advisory."""
    payload = _validated(P1CoreDemoRequestSerializer, request.data)
    identifier = payload.get("identifier", "+919812345678")
    transcript = payload.get(
        "transcript",
        "Sir this is CBI. Your Aadhaar is linked to money laundering. "
        "This is a digital arrest. Do not disconnect. Transfer to this RBI account.",
    )
    lang = payload.get("lang", "hi")

    scam = _run_and_correlate(
        "scam_call",
        {
            "identifier": identifier,
            "transcript": transcript,
            "audio_ref": payload.get("audio_ref", "demo_scam_call.wav"),
            "edge": True,
        },
    )
    shield = _run_and_correlate(
        "citizen_shield",
        {
            "identifier": identifier,
            "message": transcript,
            "lang": lang,
            "edge": True,
            "offline": True,
        },
    )
    return Response(
        {
            "demo": "p1_core_scam_call_to_shield",
            "identifier": identifier,
            "offline_proof": {
                "edge_requested": True,
                "network_required": False,
                "runtime": shield.get("edge_runtime") or shield.get("event", {}).get("payload", {}).get("edge_runtime"),
            },
            "scam_call": scam,
            "citizen_shield": shield,
            "same_script_pattern": scam.get("matched_pattern")
            == shield.get("matched_script", {}).get("pattern_id"),
        }
    )


@extend_schema(
    request=GeoHotspotRequestSerializer,
    responses=GenericAgentResponseSerializer,
    tags=["agents"],
)
@api_view(["GET", "POST"])
def geo_hotspots(request):
    payload = _validated(GeoHotspotRequestSerializer, request.data) if request.method == "POST" else {}
    return Response(_run_and_correlate("geo_command", payload))


@extend_schema(responses=AgentStatusSerializer(many=True), tags=["status"])
@api_view(["GET"])
def agents_status(request):
    """Health rail data: latest status per registered agent."""
    rows = []
    for name in AGENT_REGISTRY:
        last = AgentHealth.objects.filter(agent=name).order_by("-created_at").first()
        rows.append({
            "agent": name,
            "status": last.status if last else "unknown",
            "detail": last.detail if last else "",
            "fallback_used": last.fallback_used if last else "",
            "has_fallback": AGENT_REGISTRY[name].get("fallback") is not None,
            "updated_at": last.created_at.isoformat() if last else None,
        })
    return Response(rows)


@extend_schema(responses=EventsHistorySerializer, tags=["history"])
@api_view(["GET"])
def events_history(request):
    limit = int(request.query_params.get("limit", 50))
    events = TrustEvent.objects.all()[:limit]
    fused = FusedTrustRiskRecord.objects.all()[:limit]
    return Response({
        "events": [
            {
                "module": e.module, "signal": e.signal, "identifier": e.identifier,
                "confidence": e.confidence, "route": e.route, "payload": e.payload,
                "ts": e.ts.isoformat(),
            }
            for e in events
        ],
        "fused": [
            {
                "identifier": f.identifier, "score": f.score, "modules": f.modules,
                "ts": f.ts.isoformat(),
            }
            for f in fused
        ],
    })


@extend_schema(responses=EvidencePacketSerializer(many=True), tags=["evidence"])
@api_view(["GET"])
def evidence_packets(request):
    packets = EvidencePacket.objects.all()[:50]
    return Response([
        {
            "id": p.id, "identifier": p.identifier, "title": p.title,
            "status": p.status, "body": p.body, "created_at": p.created_at.isoformat(),
        }
        for p in packets
    ])
