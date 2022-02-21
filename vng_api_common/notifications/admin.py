from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from requests.exceptions import RequestException
from solo.admin import SingletonModelAdmin
from zds_client.client import ClientError

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

        try:
            sub.register()
        except (ClientError, RequestException) as e:
            messages.error(
                request,
                _(
                    "Something went wrong while registering subscription for {callback}: {exception}"
                ).format(callback=sub.callback_url, exception=e),
            )


register_webhook.short_description = _("Register the webhooks")  # noqa


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("callback_url", "channels", "_subscription")
    actions = [register_webhook]
