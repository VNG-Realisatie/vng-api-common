from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema


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
                "URL reference to this object. "
                "This is the unique identification and location of this object."
            ),
        }
