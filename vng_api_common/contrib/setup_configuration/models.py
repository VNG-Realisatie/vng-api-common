from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from vng_api_common.authorizations.models import Applicatie
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


class SingleApplicatieConfigurationModel(ConfigurationModel):
    client_ids: list[str]

    class Meta:
        django_model_refs = {
            Applicatie: ["uuid", "client_ids", "label", "heeft_alle_autorisaties"]
        }


class ApplicatieConfigurationModel(ConfigurationModel):
    items: list[SingleApplicatieConfigurationModel] = Field(default_factory=list)
