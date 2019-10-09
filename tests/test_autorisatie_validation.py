import pytest
from rest_framework.serializers import ValidationError

from vng_api_common.authorizations.validators import AutorisatieValidator


def test_component_not_in_mapping_is_valid():
    AutorisatieValidator()({"component": "ac", "scopes": []})
    AutorisatieValidator()({"component": "ztc", "scopes": []})
    AutorisatieValidator()({"component": "nrc", "scopes": []})


def test_zrc_fields_required_with_zaken_scopes():
    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(
            {
                "component": "zrc",
                "scopes": ["zaken.lezen", "notificaties.publiceren"],
                "max_vertrouwelijkheidaanduiding": "",
                "zaaktype": "test",
            }
        )

    error = err.value.detail

    assert "max_vertrouwelijkheidaanduiding" in error
    assert error["max_vertrouwelijkheidaanduiding"].code == "required"

    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(
            {
                "component": "zrc",
                "scopes": ["zaken.lezen", "notificaties.publiceren"],
                "max_vertrouwelijkheidaanduiding": "openbaar",
                "zaaktype": "",
            }
        )

    error = err.value.detail

    assert "zaaktype" in error
    assert error["zaaktype"].code == "required"


def test_zrc_fields_not_required_without_zaken_scopes():
    AutorisatieValidator()(
        {
            "component": "zrc",
            "scopes": ["notificaties.publiceren"],
            "max_vertrouwelijkheidaanduiding": "",
            "zaaktype": "test",
        }
    )

    AutorisatieValidator()(
        {
            "component": "zrc",
            "scopes": ["notificaties.publiceren"],
            "max_vertrouwelijkheidaanduiding": "openbaar",
            "zaaktype": "",
        }
    )


def test_drc_fields_required_with_documenten_scopes():
    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(
            {
                "component": "drc",
                "scopes": ["documenten.lezen", "notificaties.publiceren"],
                "max_vertrouwelijkheidaanduiding": "",
                "informatieobjecttype": "test",
            }
        )

    error = err.value.detail

    assert "max_vertrouwelijkheidaanduiding" in error
    assert error["max_vertrouwelijkheidaanduiding"].code == "required"

    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(
            {
                "component": "drc",
                "scopes": ["documenten.lezen", "notificaties.publiceren"],
                "max_vertrouwelijkheidaanduiding": "openbaar",
                "informatieobjecttype": "",
            }
        )

    error = err.value.detail

    assert "informatieobjecttype" in error
    assert error["informatieobjecttype"].code == "required"


def test_drc_fields_not_required_without_documenten_scopes():
    AutorisatieValidator()(
        {
            "component": "drc",
            "scopes": ["notificaties.publiceren"],
            "max_vertrouwelijkheidaanduiding": "",
            "informatieobjecttype": "test",
        }
    )

    AutorisatieValidator()(
        {
            "component": "drc",
            "scopes": ["notificaties.publiceren"],
            "max_vertrouwelijkheidaanduiding": "openbaar",
            "informatieobjecttype": "",
        }
    )


def test_brc_field_required_with_besluiten_scopes():
    with pytest.raises(ValidationError) as err:
        AutorisatieValidator()(
            {
                "component": "brc",
                "scopes": ["besluiten.lezen", "notificaties.publiceren"],
                "besluittype": "",
            }
        )

    error = err.value.detail

    assert "besluittype" in error
    assert error["besluittype"].code == "required"


def test_brc_field_not_required_without_besluiten_scopes():
    AutorisatieValidator()(
        {"component": "brc", "scopes": ["notificaties.publiceren"], "besluittype": ""}
    )
