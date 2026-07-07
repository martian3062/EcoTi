from django.contrib import admin

from .models import AdvisoryChunk, AdvisorySource


@admin.register(AdvisorySource)
class AdvisorySourceAdmin(admin.ModelAdmin):
    list_display = ("authority", "title", "origin", "fetched_at")
    list_filter = ("authority", "origin")


@admin.register(AdvisoryChunk)
class AdvisoryChunkAdmin(admin.ModelAdmin):
    list_display = ("source", "ordinal")
    search_fields = ("text",)
