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
        extra_kwargs = {
            "identifier": {"examples": ["open-notificaties-prod"]},
            "secret": {"examples": ["modify-this"]},
        }


class JWTSecretsConfigurationModel(ConfigurationModel):
    items: list[SingleJWTSecretConfigurationModel] = Field()


class SingleApplicatieConfigurationModel(ConfigurationModel):
    client_ids: list[str]

    class Meta:
        django_model_refs = {
            Applicatie: ["uuid", "client_ids", "label", "heeft_alle_autorisaties"]
        }
        extra_kwargs = {
            "client_ids": {"examples": [["open-notificaties-prod"]]},
            "label": {"examples": ["Open Notificaties (productie)"]},
        }


class ApplicatieConfigurationModel(ConfigurationModel):
    items: list[SingleApplicatieConfigurationModel]
