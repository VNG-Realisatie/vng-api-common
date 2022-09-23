from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class DurationFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.fields.DurationField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        schema = {
            **default_schema,
            "format": "duration",
        }

        label = getattr(self.target, "label", None)
        return {**schema, "title": label} if label else schema
