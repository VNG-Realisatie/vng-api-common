import logging

from django.apps import AppConfig
from django.db import models
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from . import fields
from .choices import TextChoicesWithDescriptions, ensure_description_exists
from .serializers import DurationField, LengthHyperlinkedRelatedField

try:
    from relativedeltafield import RelativeDeltaField
except ImportError:
    RelativeDeltaField = None

# https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types
# and https://github.com/OAI/OpenAPI-Specification/issues/845 - format: duration
# is collected somewhere so there's precedent
FORMAT_DURATION = "duration"

logger = logging.getLogger(__name__)


class CommonGroundAPICommonConfig(AppConfig):
    name = "vng_api_common"
    label = "vng_api_common"  # for backwards compatibility

    def ready(self):
        from . import checks  # noqa
        from . import schema  # noqa
        from .caching import signals  # noqa
        from .extensions import gegevensgroep, hyperlink, polymorphic, query  # noqa

        register_serializer_field()
        set_custom_hyperlinkedmodelserializer_field()
        set_charfield_error_messages()
        ensure_text_choice_descriptions(TextChoicesWithDescriptions)
        register_geojson_field_extension()
        register_base64_field_extension()


def register_serializer_field():
    mapping = serializers.ModelSerializer.serializer_field_mapping
    mapping[models.DurationField] = DurationField
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


def ensure_text_choice_descriptions(text_choice_class):
    ensure_description_exists(text_choice_class)

    for cls in text_choice_class.__subclasses__():
        ensure_text_choice_descriptions(cls)


def register_geojson_field_extension() -> None:
    """
    register GeoJSONGeometry extension only if rest_framework_gis is
    installed
    """
    try:
        from rest_framework_gis.fields import GeometryField  # noqa
    except ImportError:
        logger.debug(
            "Could not import djangorestframework-gis, skipping "
            "GeometryFieldExtension registration."
        )
        return

    from .extensions import geojson  # noqa


def register_base64_field_extension() -> None:
    """
    register Base64FileFileFieldExtension extension only if drf_extra_fields is
    installed
    """
    try:
        from drf_extra_fields.fields import Base64FileField  # noqa
    except ImportError:
        logger.debug(
            "Could not import drf-extra-fields, skipping "
            "Base64FileFileFieldExtension registration."
        )
        return

    from .extensions import file  # noqa
