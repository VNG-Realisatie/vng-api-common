from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import AuthorizationsConfig


@admin.register(AuthorizationsConfig)
class AuthorizationsConfigAdmin(SingletonModelAdmin):
    list_display = ('api_root', 'component',)
