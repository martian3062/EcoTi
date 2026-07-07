from django.contrib import admin

from .models import AgentHealth, EvidencePacket, FraudReport, FusedTrustRiskRecord, TrustEvent


@admin.register(FraudReport)
class FraudReportAdmin(admin.ModelAdmin):
    list_display = ("number", "category", "amount_lost", "channel", "created_at")
    list_filter = ("category", "channel")
    search_fields = ("number", "description")


@admin.register(TrustEvent)
class TrustEventAdmin(admin.ModelAdmin):
    list_display = ("module", "signal", "identifier", "confidence", "route", "ts")
    list_filter = ("module", "route")
    search_fields = ("identifier", "signal")


@admin.register(FusedTrustRiskRecord)
class FusedTrustRiskAdmin(admin.ModelAdmin):
    list_display = ("identifier", "score", "ts")
    search_fields = ("identifier",)


@admin.action(description="Approve selected evidence packets")
def approve_packets(modeladmin, request, queryset):
    queryset.update(status="approved", approved_by=request.user.get_username())


@admin.register(EvidencePacket)
class EvidencePacketAdmin(admin.ModelAdmin):
    list_display = ("identifier", "title", "status", "approved_by", "created_at")
    list_filter = ("status",)
    search_fields = ("identifier", "title")
    actions = [approve_packets]


@admin.register(AgentHealth)
class AgentHealthAdmin(admin.ModelAdmin):
    list_display = ("agent", "status", "fallback_used", "detail", "created_at")
    list_filter = ("agent", "status")
