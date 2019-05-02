import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..constants import ComponentTypes, VertrouwelijkheidsAanduiding
from ..fields import VertrouwelijkheidsAanduidingField
from ..models import APIMixin, ClientConfig


class AuthorizationsConfig(ClientConfig):
    component = models.CharField(
        _("component"), max_length=50, default=ComponentTypes.zrc,
        choices=ComponentTypes.choices
    )

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")

    def __init__(self, *args, **kwargs):
        # set api_root default value
        api_root_field = self._meta.get_field('api_root')
        api_root_field.default = 'https://ref.tst.vng.cloud/ac/api/v1'

        super().__init__(*args, **kwargs)


class Applicatie(APIMixin, models.Model):
    """
    Client level of authorization
    """
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unique resource identifier (UUID4)"
    )
    client_ids = ArrayField(
        models.CharField(max_length=50),
        help_text=_("Comma-separated list of identifiers used for authentication")
    )
    label = models.CharField(
        max_length=100,
        help_text=_("A human readable representation of the application")
    )
    heeft_alle_autorisaties = models.BooleanField(
        default=False,
        help_text=_("Globally allows everything")
    )

    def __str__(self):
        return f'Applicatie ({self.label})'


class Autorisatie(APIMixin, models.Model):
    applicatie = models.ForeignKey(
        'Applicatie',
        on_delete=models.CASCADE,
        related_name='autorisaties'
    )
    component = models.CharField(
        max_length=50,
        help_text=_("Name of the component to authorize")
    )
    zaaktype = models.URLField(
        help_text="Url of the zaaktype that is allowed",
        max_length=1000
    )
    scopes = ArrayField(
        models.CharField(max_length=100),
        help_text=_("Comma-separated list of identifiers used for authentication")
    )
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingField(
        help_text=_("Maximum level of confidentiality that is allowed")
    )

    def satisfy_vertrouwelijkheid(self, vertrouwelijkheidaanduiding: str) -> bool:
        max_confid_level = VertrouwelijkheidsAanduiding.get_choice(self.max_vertrouwelijkheidaanduiding).order
        provided_confid_level = VertrouwelijkheidsAanduiding.get_choice(vertrouwelijkheidaanduiding).order
        return max_confid_level >= provided_confid_level
