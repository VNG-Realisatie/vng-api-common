import pytest

from vng_api_common.checks import enum_value_ok


@pytest.mark.parametrize(
    "value",
    ["CAPS", "PartialCaps", "dash-instead-of-underscore", "non_áscii_character"],
)
def test_invalid_enum_values(value: str):
    assert enum_value_ok(value) is False


@pytest.mark.parametrize(
    "value", ["lowercased", "dashes_in_word", "a_number_0_is_okay"]
)
def test_valid_enum_values(value: str):
    assert enum_value_ok(value) is True
