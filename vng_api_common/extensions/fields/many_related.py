from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class ManyRelatedFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.relations.ManyRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        return {**default_schema, "uniqueItems": True}
