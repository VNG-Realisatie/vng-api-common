from django.db import models

from drf_spectacular.contrib.django_filters import DjangoFilterExtension, _NoHint
from drf_spectacular.drainage import get_override, has_override, warn
from drf_spectacular.utils import OpenApiParameter, extend_schema_field
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.plumbing import (
    build_array_type,
    build_basic_type,
    build_parameter_type,
    force_instance,
    is_basic_type,
    is_field,
)

from vng_api_common.filters import URLModelChoiceFilter
from vng_api_common.utils import underscore_to_camel


class CamelizeFilterExtension(DjangoFilterExtension):
    priority = 1

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        """
        camelize query parameters
        """
        parameters = super().get_schema_operation_parameters(
            auto_schema, *args, **kwargs
        )

        for parameter in parameters:
            parameter["name"] = underscore_to_camel(parameter["name"])

        return parameters
