import uuid
from urllib.parse import urljoin

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from zds_client import ClientAuth

from ..client import get_client
from ..decorators import field_default
from ..models import APICredential, ClientConfig


@field_default("api_root", "https://notificaties-api.vng.cloud/api/v1/")
class NotificationsConfig(ClientConfig):
    class Meta:
        verbose_name = _("Notificatiescomponentconfiguratie")

    def get_auth(self) -> ClientAuth:
        auth = APICredential.get_auth(self.api_root)
        return auth


class Subscription(models.Model):
    """
    A single subscription.

    TODO: on change/update, update the subscription
    """

    config = models.ForeignKey("NotificationsConfig", on_delete=models.CASCADE)

    callback_url = models.URLField(
        _("callback url"), help_text=_("Where to send the notifications (webhook url)")
    )
    client_id = models.CharField(
        _("client ID"),
        max_length=50,
        help_text=_("Client ID to construct the auth token"),
    )
    secret = models.CharField(
        _("client secret"),
        max_length=50,
        help_text=_("Secret to construct the auth token"),
    )
    channels = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_("channels"),
        help_text=_("Comma-separated list of channels to subscribe to"),
    )

    _subscription = models.URLField(
        _("NC subscription"),
        blank=True,
        editable=False,
        help_text=_("Subscription as it is known in the NC"),
    )

    class Meta:
        verbose_name = _("Webhook subscription")
        verbose_name_plural = _("Webhook subscriptions")

    def __str__(self):
        return f"{', '.join(self.channels)} - {self.callback_url}"

    def register(self) -> None:
        """
        Registers the webhook with the notification component.
        """
        dummy_detail_url = urljoin(self.config.api_root, f"foo/{uuid.uuid4()}")
        client = get_client(dummy_detail_url)

        # This authentication is for the NC to call us. Thus, it's *not* for
        # calling the NC to create a subscription.
        self_auth = ClientAuth(
            client_id=self.client_id,
            secret=self.secret,
        )
        data = {
            "callbackUrl": self.callback_url,
            "auth": self_auth.credentials()["Authorization"],
            "kanalen": [
                {
                    "naam": channel,
                    # FIXME: You need to be able to configure these.
                    "filters": {},
                }
                for channel in self.channels
            ],
        }

        # register the subscriber
        subscriber = client.create("abonnement", data=data)

        self._subscription = subscriber["url"]
        self.save(update_fields=["_subscription"])
