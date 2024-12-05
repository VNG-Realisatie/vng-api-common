from django_setup_configuration.configuration import BaseConfigurationStep

from vng_api_common.models import JWTSecret

from .models import JWTSecretsConfigurationModel


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
