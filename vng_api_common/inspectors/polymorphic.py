"""
Introspect polymorphic resources

Bulk of the code taken from https://github.com/axnsan12/drf-yasg/issues/100
"""
from drf_yasg import openapi
from drf_yasg.errors import SwaggerGenerationError
from drf_yasg.inspectors.base import NotHandled
from drf_yasg.inspectors.field import (
    CamelCaseJSONFilter,
    ReferencingSerializerInspector,
)

from ..polymorphism import PolymorphicSerializer
from ..utils import underscore_to_camel


class PolymorphicSerializerInspector(
    CamelCaseJSONFilter, ReferencingSerializerInspector
):
    def field_to_swagger_object(
        self, field, swagger_object_type, use_references, **kwargs
    ):
        SwaggerType, ChildSwaggerType = self._get_partial_types(
            field, swagger_object_type, use_references, **kwargs
        )

        if not isinstance(field, PolymorphicSerializer):
            return NotHandled

        if not getattr(field, "discriminator", None):
            raise SwaggerGenerationError(
                "'PolymorphicSerializer' derived serializers need to have 'discriminator' set"
            )

        base_schema_ref = super().field_to_swagger_object(
            field, swagger_object_type, use_references, **kwargs
        )
        if not isinstance(base_schema_ref, openapi.SchemaRef):
            raise SwaggerGenerationError(
                "discriminator inheritance requires model references"
            )

        base_schema = base_schema_ref.resolve(self.components)  # type: openapi.Schema
        base_schema.discriminator = underscore_to_camel(
            field.discriminator.discriminator_field
        )

        for value, serializer in field.discriminator.mapping.items():
            if serializer is None:
                allof_derived = openapi.Schema(
                    type=openapi.TYPE_OBJECT, all_of=[base_schema_ref]
                )
            else:
                derived_ref = self.probe_field_inspectors(
                    serializer, openapi.Schema, use_references=True
                )
                if not isinstance(derived_ref, openapi.SchemaRef):
                    raise SwaggerGenerationError(
                        "discriminator inheritance requies model references"
                    )

                allof_derived = openapi.Schema(
                    type=openapi.TYPE_OBJECT, all_of=[base_schema_ref, derived_ref]
                )
            if not self.components.has(value, scope=openapi.SCHEMA_DEFINITIONS):
                self.components.set(
                    value, allof_derived, scope=openapi.SCHEMA_DEFINITIONS
                )

        return base_schema_ref
