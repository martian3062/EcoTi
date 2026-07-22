"""Persistence for events, fused risks, evidence packets and agent health.

Django admin doubles as the free audit/evidence-review UI (human-approval gate).
"""
from django.db import models


class TrustEvent(models.Model):
    """A persisted A2A event (one signal from one module)."""

    module = models.CharField(max_length=64, db_index=True)
    signal = models.CharField(max_length=64)
    identifier = models.CharField(max_length=128, db_index=True, blank=True, default="")
    confidence = models.FloatField(default=0.0)
    route = models.CharField(max_length=16, default="cloud")
    payload = models.JSONField(default=dict)
    ts = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ts"]

    def __str__(self):
        return f"{self.module}/{self.signal} {self.identifier} ({self.confidence:.2f})"


class FusedTrustRiskRecord(models.Model):
    """A persisted fused TrustRisk (>= N correlated signals)."""

    identifier = models.CharField(max_length=128, db_index=True)
    score = models.FloatField()
    modules = models.JSONField(default=list)
    signals = models.JSONField(default=list)
    ts = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ts"]

    def __str__(self):
        return f"FusedTrustRisk {self.identifier} score={self.score:.2f}"


class EvidencePacket(models.Model):
    """Auditable, court-admissible evidence draft — gated behind human approval."""

    STATUS = [
        ("pending_approval", "Pending human approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    fused_risk = models.ForeignKey(
        FusedTrustRiskRecord, on_delete=models.CASCADE, related_name="packets", null=True
    )
    identifier = models.CharField(max_length=128, db_index=True)
    title = models.CharField(max_length=200)
    body = models.JSONField(default=dict)  # call metadata + graph + timestamps
    status = models.CharField(max_length=24, choices=STATUS, default="pending_approval")
    approved_by = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"EvidencePacket {self.identifier} [{self.status}]"


class OsintCache(models.Model):
    """TTL cache for OSINT footprint lookups (rate-limit friendly)."""

    kind = models.CharField(max_length=24, db_index=True)
    identifier = models.CharField(max_length=256, db_index=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField()

    class Meta:
        unique_together = ("kind", "identifier")
        ordering = ["-created_at"]

    def __str__(self):
        return f"OsintCache {self.kind}:{self.identifier}"


class FraudReport(models.Model):
    """A citizen-submitted fraud report. Reported numbers become a community
    watchlist signal that raises the risk of future number checks."""

    CATEGORIES = [
        ("digital_arrest", "Digital arrest / fake officer"),
        ("kyc_otp", "KYC / OTP / bank fraud"),
        ("courier", "Courier / parcel seizure"),
        ("upi_refund", "UPI / refund / remote access"),
        ("investment", "Investment / job / lottery scam"),
        ("other", "Other"),
    ]
    number = models.CharField(max_length=32, db_index=True)
    category = models.CharField(max_length=32, choices=CATEGORIES, default="other")
    description = models.TextField(blank=True, default="")
    amount_lost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reporter_contact = models.CharField(max_length=128, blank=True, default="")
    channel = models.CharField(max_length=32, blank=True, default="web")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.number} [{self.category}]"


class AgentHealth(models.Model):
    """Watchdog/planner record: agent health + every self-heal reroute."""

    STATUS = [
        ("healthy", "Healthy"),
        ("degraded", "Degraded (fallback active)"),
        ("crashed", "Crashed"),
        ("restarted", "Restarted"),
    ]
    agent = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS, default="healthy")
    detail = models.CharField(max_length=300, blank=True, default="")
    fallback_used = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent}: {self.status}"
