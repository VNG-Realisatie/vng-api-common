from django.core.exceptions import ValidationError

import pytest

from vng_api_common.validators import AlphanumericExcludingDiacritic


@pytest.mark.parametrize("value", ["foo$", "aëeeei", "no spaces allowed"])
def test_alphanumeric_validator_error_invalid_input(value):
    validator = AlphanumericExcludingDiacritic()

    with pytest.raises(ValidationError):
        validator(value)


@pytest.mark.parametrize(
    "value",
    [
        "simple",
        "dashes-are-ok",
        "underscores_are_too",
        "let_us_not_forget_about_numb3rs",
    ],
)
def test_alphanumeric_validator_error_valid_input(value):
    validator = AlphanumericExcludingDiacritic()
    try:
        validator(value)
    except ValidationError:
        pytest.fail("Should have passed validation")


def test_equality_validator_instances():
    validator1 = AlphanumericExcludingDiacritic()
    validator2 = AlphanumericExcludingDiacritic()

    assert validator1 == validator2
