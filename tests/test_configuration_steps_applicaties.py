import pytest
from django_setup_configuration.test_utils import execute_single_step

from vng_api_common.authorizations.models import Applicatie
from vng_api_common.contrib.setup_configuration.steps import ApplicatieConfigurationStep

CONFIG_FILE_PATH = "tests/files/setup_config_applicaties.yaml"


@pytest.mark.django_db
def test_execute_configuration_step_success():
    execute_single_step(ApplicatieConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert Applicatie.objects.count() == 2

    applicatie1, applicatie2 = Applicatie.objects.all()

    assert str(applicatie1.uuid) == "78591bab-9a00-4887-849c-53b21a67782f"
    assert applicatie1.client_ids == ["user-id", "user-id2"]
    assert applicatie1.label == "applicatie1"
    assert applicatie1.heeft_alle_autorisaties is True

    assert str(applicatie2.uuid) == "fa0f6d18-5900-4d74-aad4-a748afb2c505"
    assert applicatie2.client_ids == ["user-id2"]
    assert applicatie2.label == "applicatie2"
    assert applicatie2.heeft_alle_autorisaties is True


@pytest.mark.django_db
def test_execute_configuration_step_update_existing():
    Applicatie.objects.create(
        uuid="78591bab-9a00-4887-849c-53b21a67782f",
        client_ids=["old-user-id"],
        label="old applicatie1",
    )
    Applicatie.objects.create(
        uuid="fa0f6d18-5900-4d74-aad4-a748afb2c505",
        client_ids=["old-user-id2"],
        label="old applicatie2",
    )

    execute_single_step(ApplicatieConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    assert Applicatie.objects.count() == 2

    applicatie1, applicatie2 = Applicatie.objects.all()

    assert str(applicatie1.uuid) == "78591bab-9a00-4887-849c-53b21a67782f"
    assert applicatie1.client_ids == ["user-id", "user-id2"]
    assert applicatie1.label == "applicatie1"
    assert applicatie1.heeft_alle_autorisaties is True

    assert str(applicatie2.uuid) == "fa0f6d18-5900-4d74-aad4-a748afb2c505"
    assert applicatie2.client_ids == ["user-id2"]
    assert applicatie2.label == "applicatie2"
    assert applicatie2.heeft_alle_autorisaties is True


@pytest.mark.django_db
def test_execute_configuration_step_idempotent():
    def make_assertions():
        assert Applicatie.objects.count() == 2

        applicatie1, applicatie2 = Applicatie.objects.all()

        assert str(applicatie1.uuid) == "78591bab-9a00-4887-849c-53b21a67782f"
        assert applicatie1.client_ids == ["user-id", "user-id2"]
        assert applicatie1.label == "applicatie1"
        assert applicatie1.heeft_alle_autorisaties is True

        assert str(applicatie2.uuid) == "fa0f6d18-5900-4d74-aad4-a748afb2c505"
        assert applicatie2.client_ids == ["user-id2"]
        assert applicatie2.label == "applicatie2"
        assert applicatie2.heeft_alle_autorisaties is True

    execute_single_step(ApplicatieConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()

    execute_single_step(ApplicatieConfigurationStep, yaml_source=CONFIG_FILE_PATH)

    make_assertions()
