import logging

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.types import OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING as TYPES_MAP

logger = logging.getLogger(__name__)


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
            return default_schema

        type_info = OPENAPI_TYPE_MAPPING[type_]

        return {
            **default_schema,
            **type_info,
        }
