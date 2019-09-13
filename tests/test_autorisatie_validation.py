import pytest
from rest_framework.serializers import ValidationError

from vng_api_common.authorizations.validators import AutorisatieValidator


def required_fields_test(required_field: str, autorisatie: dict):
    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(autorisatie)

    error = err.value.detail

    assert required_field in error
    assert error[required_field].code == "required"


def test_component_not_in_mapping_is_valid():
    AutorisatieValidator()({"component": "ac", "scopes": []})
    AutorisatieValidator()({"component": "ztc", "scopes": []})
    AutorisatieValidator()({"component": "nrc", "scopes": []})


def test_zrc_required_fields():
    required_fields_test(
        "max_vertrouwelijkheidaanduiding",
        {
            "component": "zrc",
            "scopes": [],
            "max_vertrouwelijkheidaanduiding": "",
            "zaaktype": "test",
        },
    )

    required_fields_test(
        "zaaktype",
        {
            "component": "zrc",
            "scopes": [],
            "max_vertrouwelijkheidaanduiding": "openbaar",
            "zaaktype": "",
        },
    )


def test_drc_required_fields():
    required_fields_test(
        "max_vertrouwelijkheidaanduiding",
        {
            "component": "drc",
            "scopes": [],
            "max_vertrouwelijkheidaanduiding": "",
            "informatieobjecttype": "test",
        },
    )

    required_fields_test(
        "informatieobjecttype",
        {
            "component": "drc",
            "scopes": [],
            "max_vertrouwelijkheidaanduiding": "openbaar",
            "informatieobjecttype": "",
        },
    )


def test_brc_required_fields():
    required_fields_test(
        "besluittype", {"component": "brc", "scopes": [], "besluittype": ""}
    )
