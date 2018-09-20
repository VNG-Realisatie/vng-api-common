from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

import requests
from rest_framework import serializers, validators
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


class URLValidator:
    """
    Validate that the URL actually resolves to a HTTP 200

    Any init parameters are passed down to the underlying link_fetcher
    """
    message = _('The URL {url} responded with HTTP {status_code}. Please provide a valid URL.')
    code = 'bad-url'

    def __init__(self, **extra):
        self.extra = extra

    def __call__(self, value: str):
        link_fetcher = import_string(settings.LINK_FETCHER)

        response = link_fetcher(value, **self.extra)
        if response.status_code != 200:
            raise serializers.ValidationError(
                self.message.format(status_code=response.status_code, url=value),
                code=self.code
            )


class InformatieObjectUniqueValidator(validators.UniqueTogetherValidator):
    def __init__(self, parent_field, field: str):
        self.parent_field = parent_field
        self.field = field
        super().__init__(None, (parent_field, field))

    def set_context(self, serializer_field):
        serializer = serializer_field.parent
        super().set_context(serializer)

        self.queryset = serializer.Meta.model._default_manager.all()
        self.parent_object = serializer.context['parent_object']

    def __call__(self, informatieobject: str):
        attrs = {
            self.parent_field: self.parent_object,
            self.field: informatieobject,
        }
        super().__call__(attrs)


class ObjectInformatieObjectValidator:
    """
    Validate that the INFORMATIEOBJECT is linked already in the DRC.
    """
    message = _('Het informatieobject is in het DRC nog niet gerelateerd aan dit object.')
    code = 'inconsistent-relation'

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.parent_object = serializer.context['parent_object']
        self.request = serializer.context['request']

    def __call__(self, informatieobject: str):
        object_url = self.parent_object.get_absolute_api_url(self.request)

        # dynamic so that it can be mocked in tests easily
        Client = import_string(settings.ZDS_CLIENT_CLASS)
        client = Client.from_url(informatieobject, settings.BASE_DIR)
        try:
            oios = client.list('objectinformatieobject', query_params={
                'informatieobject': informatieobject,
                'object': object_url,
            })
        except requests.HTTPError as exc:
            raise serializers.ValidationError(
                exc.args[0],
                code='relation-validation-error'
            ) from exc

        if len(oios) == 0:
            raise serializers.ValidationError(self.message, code=self.code)


@deconstructible
class UntilNowValidator:
    """
    Validate a datetime to not be in the future.

    This means that `now` is included.
    """
    message = _("Ensure this value is not in the future.")
    code = 'future_not_allowed'

    @property
    def limit_value(self):
        return timezone.now()

    def __call__(self, value):
        if value > self.limit_value:
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.message == other.message and
            self.code == other.code
        )


class UniekeIdentificatieValidator:
    """
    Valideer dat de identificatie binnen de organisatie uniek is.

    Indien de identificatie niet expliciet opgegeven is, wordt ervan uitgegaan
    dat de identificatie-generator uniciteit garandeert.

    :param organisatie_field: naam van het veld dat de organisatie RSIN bevat
    :param identificatie_field: naam van het veld dat de identificatie bevat
    """
    message = _('Deze identificatie bestaat al binnen de organisatie')
    code = 'identificatie-niet-uniek'

    def __init__(self, organisatie_field: str, identificatie_field='identificatie'):
        self.organisatie_field = organisatie_field
        self.identificatie_field = identificatie_field

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)
        self.model = serializer.Meta.model

    def __call__(self, attrs: dict):
        identificatie = attrs.get(self.identificatie_field)
        if not identificatie:
            # identification is being generated, and the generation checks for
            # uniqueness
            return

        organisatie = attrs.get(self.organisatie_field)
        pk = self.instance.pk if self.instance else None

        # if we're updating an instance, setting the current values will not
        # trigger an error because the instance-to-be-updated is excluded from
        # the queryset. If either bronorganisatie or identificatie changes,
        # and it already exists, it will raise a validation error
        combination_exists = (
            self.model.objects
            # in case of an update, exclude the current object. for a create, this
            # will be None
            .exclude(pk=pk)
            .filter(**{
                self.organisatie_field: organisatie,
                self.identificatie_field: identificatie
            })
            .exists()
        )

        if combination_exists:
            raise serializers.ValidationError(
                {self.identificatie_field: self.message},
                code=self.code
            )
