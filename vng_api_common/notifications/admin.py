from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import NotificationsConfig, Subscription


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0


@admin.register(NotificationsConfig)
class NotificationsConfigAdmin(SingletonModelAdmin):
    list_display = ("api_root", "subscriptions")
    inlines = [SubscriptionInline]

    def subscriptions(self, obj):
        urls = obj.exclude(subscription_set___subscription="").values_list(
            "subscription_set___subscription"
        )
        return ", ".join(urls)


def register_webhook(modeladmin, request, queryset):
    for sub in queryset:
        if sub._subscription:
            continue
        sub.register()


register_webhook.short_description = _("Register the webhooks")  # noqa


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("callback_url", "channels", "_subscription")
    actions = [register_webhook]
