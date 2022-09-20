from drf_spectacular.extensions import OpenApiSerializerExtension


class GegevensGroepExtension(OpenApiSerializerExtension):
    target_class = "vng_api_common.serializers.GegevensGroepSerializer"
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        schema = auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )

        if self.target.allow_null:
            schema.update(nullable=True)

        if self.target.help_text:
            schema.update(description=self.target.help_text)
        else:
            schema.pop("description", None)

        return schema
