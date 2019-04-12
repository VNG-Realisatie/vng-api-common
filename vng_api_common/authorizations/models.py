import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.fields import VertrouwelijkheidsAanduidingField
from vng_api_common.models import APIMixin


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


class Autorisatie(APIMixin, models.Model):
    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4,
        help_text="Unique resource identifier (UUID4)"
    )
    applicatie = models.ForeignKey('Applicatie', on_delete=models.CASCADE)
    zaaktype = models.URLField(
        help_text="Url of the zaaktype that is allowed",
        max_length=1000
    )
    scopes = ArrayField(
        models.CharField(max_length=100),
        help_text=_("Comma-separated list of identifiers used for authentication")
    )
    maximale_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingField(
        help_text=_("Maximum level of confidentiality that is allowed")
    )
