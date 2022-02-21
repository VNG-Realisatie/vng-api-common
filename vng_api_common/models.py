from typing import Optional, Union
from urllib.parse import urlsplit, urlunsplit

from django.db import models
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse
from solo.models import SingletonModel
from zds_client import Client, ClientAuth

from .client import get_client as _get_client


class APIMixin:
    """
    Determine the absolute URL of a resource in the API.

    Model mixin that reverses the URL-path in the API based on the
    ``uuid``-field of a model instance.
    """

    def get_absolute_api_url(self, request=None, **kwargs) -> str:
        """
        Build the absolute URL of the object in the API.
        """
        # build the URL of the informatieobject
        resource_name = self._meta.model_name

        reverse_kwargs = {"uuid": self.uuid}
        reverse_kwargs.update(**kwargs)

        url = reverse(f"{resource_name}-detail", kwargs=reverse_kwargs, request=request)
        return url


class JWTSecret(models.Model):
    """
    Store credentials of clients that want to access our API.

    Only clients that are known can access the API (if so configured).
    """

    identifier = models.CharField(
        _("client ID"),
        max_length=50,
        unique=True,
        help_text=_(
            "Client ID to identify external API's and applications that access this API."
        ),
    )
    secret = models.CharField(
        _("secret"), max_length=255, help_text=_("Secret belonging to the client ID.")
    )

    class Meta:
        verbose_name = _("client credential")
        verbose_name_plural = _("client credentials")

    def __str__(self):
        return self.identifier


class APICredential(models.Model):
    """
    Store credentials for external APIs.

    When we need to authenticate against a remote API, we need to know which
    client ID and secret to use to sign the JWT.
    """

    api_root = models.URLField(
        _("API-root"),
        unique=True,
        help_text=_(
            "URL of the external API, ending in a trailing slash. Example: https://example.com/api/v1/"
        ),
    )
    label = models.CharField(
        _("label"),
        max_length=100,
        default="",
        help_text=_("Human readable label of the external API."),
    )
    client_id = models.CharField(
        _("client ID"),
        max_length=255,
        help_text=_("Client ID to identify this API at the external API."),
    )
    secret = models.CharField(
        _("secret"), max_length=255, help_text=_("Secret belonging to the client ID.")
    )
    user_id = models.CharField(
        _("user ID"),
        max_length=255,
        help_text=_(
            "User ID to use for the audit trail. Although these external API credentials are typically used by"
            "this API itself instead of a user, the user ID is required."
        ),
    )
    user_representation = models.CharField(
        _("user representation"),
        max_length=255,
        default="",
        help_text=_("Human readable representation of the user."),
    )

    class Meta:
        verbose_name = _("external API credential")
        verbose_name_plural = _("external API credentials")

    def __str__(self):
        return self.api_root

    @classmethod
    def get_auth(cls, url: str, **kwargs) -> Union[ClientAuth, None]:
        split_url = urlsplit(url)
        scheme_and_domain = urlunsplit(split_url[:2] + ("", "", ""))

        candidates = (
            cls.objects.filter(api_root__startswith=scheme_and_domain)
            .annotate(api_root_length=Length("api_root"))
            .order_by("-api_root_length")
        )

        # select the one matching
        for candidate in candidates.iterator():
            if url.startswith(candidate.api_root):
                credentials = candidate
                break
        else:
            return None

        auth = ClientAuth(
            client_id=credentials.client_id,
            secret=credentials.secret,
            user_id=credentials.user_id,
            user_representation=credentials.user_representation,
            **kwargs,
        )
        return auth


class ClientConfig(SingletonModel):
    api_root = models.URLField(_("api root"), unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.api_root

    def save(self, *args, **kwargs):
        if not self.api_root.endswith("/"):
            self.api_root = f"{self.api_root}/"
        super().save(*args, **kwargs)

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """
        Construct a client, prepared with the required auth.
        """
        config = cls.get_solo()
        return _get_client(config.api_root, url_is_api_root=True)
