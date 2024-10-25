import uuid
from typing import Optional

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes, AuthTypes

from vng_api_common.client import Client, get_client

from ..constants import ComponentTypes, VertrouwelijkheidsAanduiding
from ..decorators import field_default
from ..fields import VertrouwelijkheidsAanduidingField
from ..models import APIMixin


class AuthorizationsConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("authorizations_api_service")


class AuthorizationsConfig(SingletonModel):
    component = models.CharField(
        _("component"),
        max_length=50,
        choices=ComponentTypes.choices,
        default=ComponentTypes.zrc,
    )

    authorizations_api_service = models.ForeignKey(
        "zgw_consumers.Service",
        limit_choices_to=dict(
            api_type=APITypes.ac,
            auth_type=AuthTypes.zgw,
        ),
        verbose_name=_("autorisations api service"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    objects = AuthorizationsConfigManager()

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """
        Construct a client, prepared with the required auth.
        """
        config = cls.get_solo()
        if config.authorizations_api_service:
            return get_client(config.authorizations_api_service.api_root)
        return None


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
