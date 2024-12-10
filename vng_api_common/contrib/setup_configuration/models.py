from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from vng_api_common.models import JWTSecret


class SingleJWTSecretConfigurationModel(ConfigurationModel):
    class Meta:
        django_model_refs = {
            JWTSecret: [
                "identifier",
                "secret",
            ]
        }


class JWTSecretsConfigurationModel(ConfigurationModel):
    items: list[SingleJWTSecretConfigurationModel] = Field(default_factory=list)
