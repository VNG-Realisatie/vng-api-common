from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import JWTSecret


@admin.register(JWTSecret)
class JWTSecretAdmin(admin.ModelAdmin):
    list_display = ("identifier",)
    search_fields = ("identifier",)
