from django.apps import AppConfig
from django.db import models
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from . import fields
from .serializers import DurationField, LengthHyperlinkedRelatedField

try:
    from relativedeltafield import RelativeDeltaField
except ImportError:
    RelativeDeltaField = None

# https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types
# and https://github.com/OAI/OpenAPI-Specification/issues/845 - format: duration
# is collected somewhere so there's precedent
FORMAT_DURATION = "duration"


class ZDSSchemaConfig(AppConfig):
    name = "vng_api_common"

    def ready(self):
        from . import checks  # noqa
        from .caching import signals  # noqa

        register_serializer_field()
        set_custom_hyperlinkedmodelserializer_field()
        set_charfield_error_messages()


def register_serializer_field():
    mapping = serializers.ModelSerializer.serializer_field_mapping
    mapping[models.fields.DurationField] = DurationField
    mapping[fields.DaysDurationField] = DurationField

    if RelativeDeltaField is not None:
        mapping[RelativeDeltaField] = DurationField


def set_custom_hyperlinkedmodelserializer_field():
    """
    Monkey-patches Django Rest Framework to avoid having to set the
    `serializer_related_field` manually for all the base classes in the code
    """
    serializers.HyperlinkedModelSerializer.serializer_related_field = (
        LengthHyperlinkedRelatedField
    )


def set_charfield_error_messages():
    """
    Monkey-patches Django forms CharField to supply error messages for min and
    max_length. If these are not specified, the serialized validation errors
    would be empty
    """
    CharField.default_error_messages.update(
        {
            "max_length": _("The value has too many characters"),
            "min_length": _("The value has too few characters"),
        }
    )
