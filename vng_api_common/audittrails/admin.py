from django.contrib import admin

from .models import AuditTrail

# Register your models here.

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['uuid']
