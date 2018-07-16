from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible

from unidecode import unidecode

from .constants import RSIN_LENGTH


@deconstructible
class AlphanumericExcludingDiacritic:
    """
    Alle alfanumerieke tekens m.u.v. diacrieten.
    """

    def __init__(self, start=0):
        self.start = start

    def __call__(self, value):
        stripped_value = value[self.start:]
        non_diactric = unidecode(stripped_value)
        non_diactric.encode('ascii')
        if stripped_value != non_diactric:
            raise ValidationError(
                'Waarde "{0}" mag geen diakrieten of non-ascii tekens bevatten{1}'.format(
                    value, ' na de eerste {0} karakters'.format(self.start) if self.start else ''
                )
            )

    def __eq__(self, other):
        return isinstance(other, AlphanumericExcludingDiacritic) and self.start == other.start


# Default validator for entire string.
alphanumeric_excluding_diacritic = AlphanumericExcludingDiacritic()


def validate_non_negative_string(value):
    """
    Validate a string containing a integer to be non-negative.
    """
    error = False
    try:
        n = int(value)
    except ValueError:
        error = True
    if error or n < 0:
        raise ValidationError('De waarde moet een niet-negatief getal zijn.')


validate_digits = RegexValidator(
    regex='^[0-9]+$', message='Waarde moet numeriek zijn.',
    code='only-digits'
)


def validate_rsin(value):
    """
    Validates that a string value is a valid RSIN number by applying the
    '11-proef' checking.

    :param value: String object representing a presumably good RSIN number.
    """
    # Initial sanity checks.
    validate_digits(value)
    if len(value) != RSIN_LENGTH:
        raise ValidationError(
            'RSIN moet %s tekens lang zijn.' % RSIN_LENGTH,
            code='invalid-length'
        )

    # 11-proef check.
    total = 0
    for multiplier, char in enumerate(reversed(value), start=1):
        if multiplier == 1:
            total += -multiplier * int(char)
        else:
            total += multiplier * int(char)

    if total % 11 != 0:
        raise ValidationError('Onjuist RSIN nummer.', code='invalid')
