import logging

from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema, OpenApiTypes
from drf_spectacular.plumbing import build_basic_type

logger = logging.getLogger(__name__)

TYPES_MAP = {
    str: OpenApiTypes.STR,
    int: OpenApiTypes.INT,
    bool: OpenApiTypes.BOOL,
}


class HyperlinkedRelatedFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "vng_api_common.serializers.LengthHyperlinkedRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema: AutoSchema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )
        return {
            **default_schema,
            "minLength": self.target.min_length,
            "maxLength": self.target.max_length,
        }


class HyperlinkedIdentityFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.serializers.HyperlinkedIdentityField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema: AutoSchema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )
        return {
            **default_schema,
            "minLength": 1,
            "maxLength": 1000,
            "description": _(
                "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
            ),
        }


class Base64FileFileFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "drf_extra_fields.fields.Base64FileField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        base64_schema = {
            **build_basic_type(OpenApiTypes.BYTE),
            "description": _("Base64 encoded binary content."),
        }

        uri_schema = {
            **build_basic_type(OpenApiTypes.URI),
            "description": _("Download URL of the binary content."),
        }

        if direction == "request":
            return base64_schema
        elif direction == "response":
            return uri_schema if not self.target.represent_in_base64 else base64_schema
