from django.contrib import admin

from .models import APICredential, JWTSecret


@admin.register(JWTSecret)
class JWTSecretAdmin(admin.ModelAdmin):
    list_display = ('identifier',)
    search_fields = ('identifier',)


@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ('api_root', 'client_id')
    search_fields = ('api_root',)
