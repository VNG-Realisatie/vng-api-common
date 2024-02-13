import logging

from django.utils.translation import gettext_lazy as _

from drf_spectacular import openapi
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.parsers import JSONParser, MultiPartParser

logger = logging.getLogger(__name__)


class AutoSchema(openapi.AutoSchema):
    method_mapping = dict(
        **openapi.AutoSchema.method_mapping,
        head="headers",
    )

    def get_override_parameters(self):
        params = super().get_override_parameters()

        # Require Content-Type headers on POST requests
        if self.method == "POST":
            mime_type_enum = [
                cls.media_type
                for cls in self.view.parser_classes
                if hasattr(cls, "media_type")
            ]
            if mime_type_enum:
                params.append(
                    OpenApiParameter(
                        name="Content-Type",
                        location=OpenApiParameter.HEADER,
                        required=True,
                        type=str,
                        enum=mime_type_enum,
                        description=_("Content type of the request body."),
                    )
                )
        return params

    def get_operation(self, *args, **kwargs):
        operation = super().get_operation(*args, **kwargs)
        return operation
