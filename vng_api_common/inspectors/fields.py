import logging

from drf_spectacular.extensions import (
    OpenApiSerializerExtension,
    OpenApiSerializerFieldExtension,
)
from drf_spectacular.plumbing import ResolvedComponent
from drf_spectacular.types import PYTHON_TYPE_MAPPING as TYPES_MAP

logger = logging.getLogger(__name__)


# TODO: verify this in schema output
class ReadOnlyFieldExtension(OpenApiSerializerFieldExtension):
    """
    Provides conversion for derived ReadOnlyField from model fields.

    This inspector looks at the type hint to determine the type/format of
    a model property.
    """

    target_class = "rest_framework.fields.ReadOnlyField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        prop = getattr(self.target.parent.Meta.model, self.target.source)
        if not isinstance(prop, property):
            return default_schema

        return_type = prop.fget.__annotations__.get("return")
        if return_type is None:  # no type annotation, too bad...
            logger.debug(
                "Missing return type annotation for prop %s on model %s",
                self.target.source,
                self.target.parent.Meta.model,
            )
            return default_schema

        type_ = TYPES_MAP.get(return_type)
        if type_ is None:
            logger.debug("Missing type mapping for %r", return_type)

        return ResolvedComponent(self.target.field_name, type_ or TYPES_MAP[str])


class HyperlinkedRelatedFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.relations.HyperlinkedRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        return {
            **default_schema,
            "description": "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object.",
            "min_length": 1,
            "max_length": 1000,
        }


class HyperlinkedIdentityFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.relations.HyperlinkedIdentityField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        return {
            **default_schema,
            "description": self.target.help_text,
            "min_length": self.target.min_length,
            "max_length": self.target.max_length,
        }


class GegevensGroepExtension(OpenApiSerializerExtension):
    target_class = "vng_api_common.serializers.GegevensGroepSerializer"
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        schema = auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )

        if self.target.allow_null:
            schema.update(nullable=True)

        if self.target.help_text:
            schema.update(description=self.target.help_text)
        else:
            schema.pop("description", None)

        return schema
