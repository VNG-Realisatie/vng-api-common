from django.contrib import admin

from .models import JWTSecret


@admin.register(JWTSecret)
class JWTSecretAdmin(admin.ModelAdmin):
    list_display = ('identifier',)
    search_fields = ('identifier',)
