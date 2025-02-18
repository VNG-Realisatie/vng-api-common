from django_setup_configuration.configuration import BaseConfigurationStep

from vng_api_common.authorizations.models import Applicatie
from vng_api_common.models import JWTSecret

from .models import ApplicatieConfigurationModel, JWTSecretsConfigurationModel


class JWTSecretsConfigurationStep(BaseConfigurationStep[JWTSecretsConfigurationModel]):
    """
    Configure credentials for Applications that need access
    """

    verbose_name = "Configuration to create credentials"
    config_model = JWTSecretsConfigurationModel
    namespace = "vng_api_common_credentials"
    enable_setting = "vng_api_common_credentials_config_enable"

    def execute(self, model: JWTSecretsConfigurationModel):
        for config in model.items:
            JWTSecret.objects.update_or_create(
                identifier=config.identifier,
                defaults={"secret": config.secret},
            )


class ApplicatieConfigurationStep(BaseConfigurationStep[ApplicatieConfigurationModel]):
    """
    Configure Applicaties used for authorization.

    .. note:: The values of ``client_ids`` must match the values of the ``identifier`` field(s)
        in the ``vng_api_common_credentials`` namespace. To give proper access to an application,
        you need to load the credentials (``identifier`` and ``secret``)
        **and** the Applicatie (``client_ids``, ``uuid``, ``label`` and permissions)
    """

    verbose_name = "Configuration to create applicaties"
    config_model = ApplicatieConfigurationModel
    namespace = "vng_api_common_applicaties"
    enable_setting = "vng_api_common_applicaties_config_enable"

    def execute(self, model: ApplicatieConfigurationModel):
        for config in model.items:
            Applicatie.objects.update_or_create(
                uuid=config.uuid,
                defaults={
                    "client_ids": config.client_ids,
                    "label": config.label,
                    "heeft_alle_autorisaties": config.heeft_alle_autorisaties,
                },
            )
