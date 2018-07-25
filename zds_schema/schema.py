from collections import OrderedDict

from drf_yasg import openapi
from drf_yasg.generators import (
    OpenAPISchemaGenerator as _OpenAPISchemaGenerator
)
from drf_yasg.inspectors import SwaggerAutoSchema
from rest_framework import serializers, status

from .search import is_search_view

TYPE_TO_FIELDMAPPING = {
    openapi.TYPE_INTEGER: serializers.IntegerField,
    openapi.TYPE_NUMBER: serializers.FloatField,
    openapi.TYPE_STRING: serializers.CharField,
    openapi.TYPE_BOOLEAN: serializers.BooleanField,
}


class AutoSchema(SwaggerAutoSchema):

    @property
    def model(self):
        qs = self.view.get_queryset()
        return qs.model

    @property
    def _is_search_view(self):
        return is_search_view(self.view)

    def get_operation_id(self, operation_keys):
        """
        Simply return the model name as lowercase string, postfixed with the operation name.
        """
        action = operation_keys[-1]
        model_name = self.model._meta.model_name
        return f"{model_name}_{action}"

    def should_page(self):
        if self._is_search_view:
            return hasattr(self.view, 'paginator')
        return super().should_page()

    def get_request_serializer(self):
        if not self._is_search_view:
            return super().get_request_serializer()

        Base = self.view.get_search_input_serializer_class()

        filter_fields = []
        for filter_backend in self.view.filter_backends:
            filter_fields += self.probe_inspectors(
                self.filter_inspectors,
                'get_filter_parameters', filter_backend()
            ) or []

        filters = {}
        for filter_field in filter_fields:
            FieldClass = TYPE_TO_FIELDMAPPING[filter_field.type]
            filters[filter_field.name] = FieldClass(
                help_text=filter_field.description,
                required=filter_field.required
            )

        SearchSerializer = type(Base.__name__, (Base,), filters)
        return SearchSerializer()

    def _get_search_responses(self):
        response_status = status.HTTP_200_OK
        response_schema = self.serializer_to_schema(self.get_view_serializer())
        schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=response_schema)
        if self.should_page():
            schema = self.get_paginated_response(schema) or schema
        return OrderedDict({str(response_status): schema})

    def get_default_responses(self) -> OrderedDict:
        if self._is_search_view:
            responses = self._get_search_responses()
            serializer = self.get_view_serializer()
        else:
            responses = super().get_default_responses()
            serializer = self.get_request_serializer() or self.get_view_serializer()

        # inject any headers
        _responses = OrderedDict()
        for status_, schema in responses.items():
            custom_headers = self.probe_inspectors(
                self.field_inspectors, 'get_response_headers',
                serializer, {'field_inspectors': self.field_inspectors},
                status=status_
            ) or None

            assert isinstance(schema, openapi.Schema.OR_REF) or schema == ''
            response = openapi.Response(
                description='',
                schema=schema or None,
                headers=custom_headers
            )
            _responses[status_] = response
        return _responses

    def add_manual_parameters(self, parameters):
        base = super().add_manual_parameters(parameters)
        if self._is_search_view:
            serializer = self.get_request_serializer()
        else:
            serializer = self.get_request_serializer() or self.get_view_serializer()
        extra = self.probe_inspectors(
            self.field_inspectors, 'get_request_header_parameters',
            serializer, {'field_inspectors': self.field_inspectors}
        ) or []
        return base + extra


class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):

    def get_path_parameters(self, path, view_cls):
        """Return a list of Parameter instances corresponding to any templated path variables.

        :param str path: templated request path
        :param type view_cls: the view class associated with the path
        :return: path parameters
        :rtype: list[openapi.Parameter]
        """
        parameters = super().get_path_parameters(path, view_cls)

        # see if we can specify UUID a bit more
        for parameter in parameters:
            # the most pragmatic of checks
            if not parameter.name.endswith('_uuid'):
                continue
            parameter.format = openapi.FORMAT_UUID
            parameter.description = "Unieke resource identifier (UUID4)"
        return parameters
