from django.contrib import admin

from .models import AuditTrail


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ("uuid", "bron", "resultaat", "applicatie_weergave")
    list_filter = ("bron", "applicatie_id", "resultaat")
    date_hierarchy = "aanmaakdatum"
