from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema


class GegevensGroepFieldExtension(OpenApiSerializerExtension):
    target_class = "vng_api_common.serializers.GegevensGroepSerializer"
    match_subclasses = True

    def map_serializer(self, auto_schema: AutoSchema, direction):
        schema = auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )

        del schema["description"]

        return schema
