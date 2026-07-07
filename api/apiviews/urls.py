from django.urls import path

from . import views

urlpatterns = [
    path("scam-call/analyze", views.scam_call_analyze),
    path("counterfeit/verify", views.counterfeit_verify),
    path("fraud-graph/score", views.fraud_graph_score),
    path("shield/assess", views.shield_assess),
    path("demo/p1-core", views.p1_core_demo),
    path("geo/hotspots", views.geo_hotspots),
    path("agents/status", views.agents_status),
    path("providers/health", views.providers_health),
    path("number/check", views.number_check),
    path("footprint", views.footprint),
    path("tor/summary", views.tor_summary),
    path("tor/anomalies", views.tor_anomalies),
    path("tor/check-ip", views.tor_check_ip),
    path("report", views.report_fraud),
    path("report/recent", views.report_recent),
    path("rag/ask", views.rag_ask),
    path("rag/sources", views.rag_sources),
    path("events", views.events_history),
    path("evidence", views.evidence_packets),
]
