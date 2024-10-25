from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse


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


class JWTSecretManager(models.Manager):
    def get_by_natural_key(self, identifier):
        return self.get(identifier=identifier)


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

    objects = JWTSecretManager()

    def natural_key(self):
        return (self.identifier,)

    class Meta:
        verbose_name = _("client credential")
        verbose_name_plural = _("client credentials")

    def __str__(self):
        return self.identifier
