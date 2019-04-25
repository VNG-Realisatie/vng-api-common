from django.contrib import admin

from .models import AuthorizationsConfig
from solo.admin import SingletonModelAdmin


@admin.register(AuthorizationsConfig)
class AuthorizationsConfigAdmin(SingletonModelAdmin):
    list_display = ('api_root', 'component',)
