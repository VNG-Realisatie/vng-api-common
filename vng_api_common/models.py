from typing import Union
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.functions import Length
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from rest_framework.reverse import reverse
from solo.models import SingletonModel
from zds_client import Client, ClientAuth


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

        reverse_kwargs = {'uuid': self.uuid}
        reverse_kwargs.update(**kwargs)

        url = reverse(
            f'{resource_name}-detail',
            kwargs=reverse_kwargs, request=request
        )
        return url


class JWTSecret(models.Model):
    """
    Store credentials of clients that want to access our API.

    Only clients that are known can access the API (if so configured).
    """
    identifier = models.CharField(_("identifier"), max_length=50, unique=True)
    secret = models.CharField(_("secret"), max_length=255)

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
    api_root = models.URLField(_("api root"), unique=True)
    label = models.CharField(_("label"), max_length=100, help_text=_("human readable label"), default='')
    client_id = models.CharField(_("client id"), max_length=255)
    secret = models.CharField(_("secret"), max_length=255)

    class Meta:
        verbose_name = _("external API credential")
        verbose_name_plural = _("external API credentials")

    def __str__(self):
        return self.api_root

    @classmethod
    def get_auth(cls, url: str, **kwargs) -> Union[ClientAuth, None]:
        split_url = urlsplit(url)
        scheme_and_domain = urlunsplit(split_url[:2] + ('', '', ''))

        candidates = (
            cls.objects
            .filter(api_root__startswith=scheme_and_domain)
            .annotate(api_root_length=Length('api_root'))
            .order_by('-api_root_length')
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
            **kwargs
        )
        return auth


class ClientConfig(SingletonModel):
    api_root = models.URLField(_("api root"), unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.api_root

    @classmethod
    def get_client(cls) -> Client:
        """
        Construct a client, prepared with the required auth.
        """
        config = cls.get_solo()
        Client = import_string(settings.ZDS_CLIENT_CLASS)

        api_root = config.api_root
        if not api_root:
            raise ImproperlyConfigured(f"Configure the API root in '{cls._meta.verbose_name}'")

        if not api_root.endswith('/'):
            api_root = f"{api_root}/"

        client = Client.from_url(api_root)
        client.base_url = api_root
        client.auth = APICredential.get_auth(api_root)

        return client
