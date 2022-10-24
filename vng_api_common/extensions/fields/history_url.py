from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class HistoryURLFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.fields.SerializerMethodField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )
        if self.target.__class__.__name__ == "HistoryURLField":
            default_schema["example"] = ["http://example.com"]
            default_schema["items"] = {"type": "string", "format": "uri"}
            default_schema["format"] = "uri"
            default_schema |= {
                "description": f"URL referenties van de {self.target.field_name} welke horen bij deze versie van het ZAAKTYPE.",
            }

        return default_schema
