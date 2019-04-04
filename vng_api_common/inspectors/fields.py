import logging

from drf_yasg import openapi
from drf_yasg.inspectors.base import NotHandled
from drf_yasg.inspectors.field import FieldInspector
from rest_framework import serializers

logger = logging.getLogger(__name__)


TYPES_MAP = {
    str: openapi.TYPE_STRING,
    int: openapi.TYPE_INTEGER,
    bool: openapi.TYPE_BOOLEAN,
}


class ReadOnlyFieldInspector(FieldInspector):
    """
    Provides conversion for derived ReadOnlyField from model fields.

    This inspector looks at the type hint to determine the type/format of
    a model property.
    """

    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)

        if isinstance(field, serializers.ReadOnlyField) and swagger_object_type == openapi.Schema:
            prop = getattr(field.parent.Meta.model, field.source)
            if not isinstance(prop, property):
                return NotHandled

            return_type = prop.fget.__annotations__.get('return')
            if return_type is None:  # no type annotation, too bad...
                logger.debug("Missing return type annotation for prop %s on model %s",
                             field.source, field.parent.Meta.model)
                return NotHandled

            type_ = TYPES_MAP.get(return_type)
            if type_ is None:
                logger.debug("Missing type mapping for %r", return_type)

            return SwaggerType(type=type_ or openapi.TYPE_STRING)

        return NotHandled
