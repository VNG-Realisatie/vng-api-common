import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..constants import ComponentTypes, VertrouwelijkheidsAanduiding
from ..decorators import field_default
from ..fields import VertrouwelijkheidsAanduidingField
from ..models import APIMixin, ClientConfig


@field_default("api_root", "https://autorisaties-api.vng.cloud/api/v1")
class AuthorizationsConfig(ClientConfig):
    component = models.CharField(
        _("component"),
        max_length=50,
        choices=ComponentTypes.choices,
        default=ComponentTypes.zrc,
    )

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")


class ApplicatieManager(models.Manager):
    def get_by_natural_key(self, uuid):
        return self.get(uuid=uuid)


class Applicatie(APIMixin, models.Model):
    """
    Client level of authorization
    """

    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4, help_text="Unique resource identifier (UUID4)"
    )
    client_ids = ArrayField(
        models.CharField(max_length=50),
        verbose_name=_("client IDs"),
        help_text=_("Komma-gescheiden lijst van consumer identifiers (hun client_id)."),
    )
    label = models.CharField(
        max_length=100,
        help_text=_(
            "Een leesbare representatie van de applicatie, voor eindgebruikers."
        ),
    )
    heeft_alle_autorisaties = models.BooleanField(
        _("heeft alle autorisaties"),
        default=False,
        help_text=_(
            "Indien alle autorisaties gegeven zijn, dan hoeven deze "
            "niet individueel opgegeven te worden. Gebruik dit alleen "
            "als je de consumer helemaal vertrouwt."
        ),
    )

    objects = ApplicatieManager()

    def natural_key(self):
        return (str(self.uuid),)

    def __str__(self):
        return f"Applicatie ({self.label})"


class AutorisatieManager(models.Manager):
    def get_by_natural_key(self, applicatie, component, scopes):
        return self.get(applicatie=applicatie, component=component, scopes=scopes)


class Autorisatie(APIMixin, models.Model):
    applicatie = models.ForeignKey(
        "Applicatie",
        on_delete=models.CASCADE,
        related_name="autorisaties",
        verbose_name=_("applicatie"),
    )
    component = models.CharField(
        _("component"),
        max_length=50,
        choices=ComponentTypes.choices,
        help_text=_("Component waarop autorisatie van toepassing is."),
    )
    scopes = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_("scopes"),
        help_text=_("Komma-gescheiden lijst van scope labels."),
    )

    # ZRC exclusive
    zaaktype = models.URLField(
        _("zaaktype"),
        help_text=_("URL naar het zaaktype waarop de autorisatie van toepassing is."),
        max_length=1000,
        blank=True,
    )

    # DRC exclusive
    informatieobjecttype = models.URLField(
        _("informatieobjecttype"),
        help_text=_(
            "URL naar het informatieobjecttype waarop de autorisatie van toepassing is."
        ),
        max_length=1000,
        blank=True,
    )

    # BRC exclusive
    besluittype = models.URLField(
        _("besluittype"),
        help_text=_(
            "URL naar het besluittype waarop de autorisatie van toepassing is."
        ),
        max_length=1000,
        blank=True,
    )

    # ZRC & DRC exclusive
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduidingField(
        help_text=_("Maximaal toegelaten vertrouwelijkheidaanduiding (inclusief)."),
        blank=True,
    )

    objects = AutorisatieManager()

    def natural_key(self):
        return (
            self.applicatie,
            self.component,
            self.scopes,
        )

    def satisfy_vertrouwelijkheid(self, vertrouwelijkheidaanduiding: str) -> bool:
        max_confid_level = VertrouwelijkheidsAanduiding.get_choice(
            self.max_vertrouwelijkheidaanduiding
        ).order
        provided_confid_level = VertrouwelijkheidsAanduiding.get_choice(
            vertrouwelijkheidaanduiding
        ).order
        return max_confid_level >= provided_confid_level
