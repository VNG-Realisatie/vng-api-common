from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import Applicatie, AuthorizationsConfig, Autorisatie


@admin.register(AuthorizationsConfig)
class AuthorizationsConfigAdmin(SingletonModelAdmin):
    list_display = ('api_root', 'component',)


@admin.register(Autorisatie)
class AutorisatieAdmin(admin.ModelAdmin):
    list_display = ('applicatie', 'component', 'zaaktype', 'scopes', 'max_vertrouwelijkheidaanduiding')


class AutorisatieInline(admin.TabularInline):
    model = Autorisatie


@admin.register(Applicatie)
class ApplicatieAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'client_ids', 'label', 'heeft_alle_autorisaties', )
    readonly_fields = ('uuid',)
    inlines = (AutorisatieInline,)
