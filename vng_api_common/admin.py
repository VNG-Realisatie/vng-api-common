from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import APICredential, JWTSecret


@admin.register(JWTSecret)
class JWTSecretAdmin(admin.ModelAdmin):
    list_display = ("identifier",)
    search_fields = ("identifier",)


@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ("label", "api_root", "client_id", "user_id")
    search_fields = ("label", "api_root")
    fieldsets = (
        (_("external API"), {"fields": ["api_root", "label"]}),
        (
            _("credentials"),
            {
                "description": _(
                    "Credentials that indicate how this API or application identifies itself at the external "
                    "API."
                ),
                "fields": ["client_id", "secret", "user_id", "user_representation"],
            },
        ),
    )
