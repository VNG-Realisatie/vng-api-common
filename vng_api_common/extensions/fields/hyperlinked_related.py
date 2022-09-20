from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class HyperlinkedRelatedFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "vng_api_common.serializers.LengthHyperlinkedRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        return {
            **default_schema,
            "description": self.target.help_text,
            "min_length": self.target.min_length,
            "max_length": self.target.max_length,
        }
