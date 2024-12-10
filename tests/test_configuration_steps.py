import pytest
from django_setup_configuration.test_utils import execute_single_step

from vng_api_common.contrib.setup_configuration.steps import JWTSecretsConfigurationStep
from vng_api_common.models import JWTSecret

CONFIG_FILE_PATH = "tests/files/setup_config_jwtsecrets.yaml"


@pytest.mark.django_db
def test_execute_configuration_step_success():
    execute_single_step(JWTSecretsConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert JWTSecret.objects.count() == 2

    credential1, credential2 = JWTSecret.objects.all()

    assert credential1.identifier == "user-id"
    assert credential1.secret == "super-secret"

    assert credential2.identifier == "user-id2"
    assert credential2.secret == "super-secret2"


@pytest.mark.django_db
def test_execute_configuration_step_update_existing():
    JWTSecret.objects.create(identifier="user-id", secret="old")
    JWTSecret.objects.create(identifier="user-id2", secret="old2")

    execute_single_step(JWTSecretsConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert JWTSecret.objects.count() == 2

    credential1, credential2 = JWTSecret.objects.all()

    assert credential1.identifier == "user-id"
    assert credential1.secret == "super-secret"

    assert credential2.identifier == "user-id2"
    assert credential2.secret == "super-secret2"


@pytest.mark.django_db
def test_execute_configuration_step_idempotent():
    def make_assertions():
        assert JWTSecret.objects.count() == 2

        credential1, credential2 = JWTSecret.objects.all()

        assert credential1.identifier == "user-id"
        assert credential1.secret == "super-secret"

        assert credential2.identifier == "user-id2"
        assert credential2.secret == "super-secret2"

    execute_single_step(JWTSecretsConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()

    execute_single_step(JWTSecretsConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()
