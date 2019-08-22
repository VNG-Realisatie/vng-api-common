from collections import OrderedDict

from django.utils.translation import ugettext as _

from drf_extra_fields.fields import Base64FieldMixin
from drf_yasg import openapi
from drf_yasg.inspectors import (
    CamelCaseJSONFilter,
    FieldInspector,
    NotHandled,
    ViewInspector,
)
from drf_yasg.utils import filter_none, get_serializer_ref_name
from rest_framework import serializers


class FileFieldInspector(CamelCaseJSONFilter):
    def get_schema(self, serializer):
        if self.method not in ViewInspector.body_methods:
            return NotHandled

        # only do this if there are base64 mixin fields
        if any(
            isinstance(field, Base64FieldMixin) for field in serializer.fields.values()
        ):
            return self.probe_field_inspectors(serializer, openapi.Schema, True)

        return NotHandled

    def field_to_swagger_object(
        self, field, swagger_object_type, use_references, **kwargs
    ):
        if isinstance(field, serializers.Serializer):
            return self._serializer_to_swagger_object(
                field, swagger_object_type, use_references, **kwargs
            )

        if not isinstance(field, Base64FieldMixin):
            return NotHandled

        SwaggerType, ChildSwaggerType = self._get_partial_types(
            field, swagger_object_type, use_references, **kwargs
        )

        type_b64 = SwaggerType(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_BASE64,
            description=_("Base64 encoded binary content."),
        )
        type_uri = SwaggerType(
            type=openapi.TYPE_STRING,
            read_only=True,
            format=openapi.FORMAT_URI,
            description=_("Download URL of the binary content."),
        )

        if swagger_object_type == openapi.Schema:
            # on writes, it's always b64
            if self.method in ViewInspector.body_methods:
                return type_b64

            # if not representing in base64, it's a link
            return type_uri if not field.represent_in_base64 else type_b64

        return NotHandled

    def _serializer_to_swagger_object(
        self, serializer, swagger_object_type, use_references, **kwargs
    ):
        if self.method not in ViewInspector.body_methods:
            return NotHandled

        if not any(
            isinstance(field, Base64FieldMixin) for field in serializer.fields.values()
        ):
            return NotHandled

        SwaggerType, ChildSwaggerType = self._get_partial_types(
            serializer, swagger_object_type, use_references, **kwargs
        )

        ref_name = get_serializer_ref_name(serializer)
        ref_name = f"{ref_name}Data" if ref_name else None

        def make_schema_definition():
            properties = OrderedDict()
            required = []
            for property_name, child in serializer.fields.items():
                prop_kwargs = {"read_only": bool(child.read_only) or None}
                prop_kwargs = filter_none(prop_kwargs)

                child_schema = self.probe_field_inspectors(
                    child, ChildSwaggerType, use_references, **prop_kwargs
                )
                properties[property_name] = child_schema

                if child.required and not getattr(child_schema, "read_only", False):
                    required.append(property_name)

            result = SwaggerType(
                type=openapi.TYPE_OBJECT,
                properties=properties,
                required=required or None,
            )
            if not ref_name and "title" in result:
                # on an inline model, the title is derived from the field name
                # but is visually displayed like the model name, which is confusing
                # it is better to just remove title from inline models
                del result.title

            # Provide an option to add manual paremeters to a schema
            # for example, to add examples
            # self.add_manual_fields(serializer, result)
            return self.process_result(result, None, None)

        if not ref_name or not use_references:
            return make_schema_definition()

        definitions = self.components.with_scope(openapi.SCHEMA_DEFINITIONS)
        definitions.setdefault(ref_name, make_schema_definition)
        return openapi.SchemaRef(definitions, ref_name)
