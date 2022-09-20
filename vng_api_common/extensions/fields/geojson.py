from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import ResolvedComponent

from vng_api_common.oas import TYPE_ARRAY, TYPE_NUMBER, TYPE_OBJECT, TYPE_STRING


class GeometryFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework_gis.fields.GeometryField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        geometry_component = ResolvedComponent(
            name="Geometry",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Geometry",
                "description": "GeoJSON geometry",
                "type": TYPE_OBJECT,
                "required": ["type"],
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1",
                },
                "properties": {
                    "type": {
                        "type": TYPE_STRING,
                        "enum": [
                            "Point",
                            "MultiPoint",
                            "LineString",
                            "MultiLineString",
                            "Polygon",
                            "MultiPolygon",
                            "Feature",
                            "FeatureCollection",
                            "GeometryCollection",
                        ],
                        "description": "The geometry type",
                    }
                },
            },
            object="Geometry",
        )

        auto_schema.registry.register_on_missing(geometry_component)

        point2d_component = ResolvedComponent(
            name="Point2D",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Point2D",
                "type": TYPE_ARRAY,
                "items": {
                    "type": TYPE_NUMBER,
                },
                "maxItems": 2,
                "minItems": 2,
            },
            object="Point2D",
        )

        auto_schema.registry.register_on_missing(point2d_component)

        point_component = ResolvedComponent(
            name="Point",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Point",
                "description": "GeoJSON point geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.2",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": point2d_component.ref,
                        },
                    },
                ],
            },
            object="Point",
        )

        auto_schema.registry.register_on_missing(point_component)

        multi_point_component = ResolvedComponent(
            name="MultiPoint",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "MultiPoint",
                "description": "GeoJSON multi-point geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.3",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": TYPE_ARRAY,
                                "items": point2d_component.ref,
                            },
                        },
                    },
                ],
            },
            object="MultiPoint",
        )

        auto_schema.registry.register_on_missing(multi_point_component)

        line_string_component = ResolvedComponent(
            name="LineString",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Line-string",
                "description": "GeoJSON line-string geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.4",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": TYPE_ARRAY,
                                "items": point2d_component.ref,
                                "minItems": 2,
                            },
                        },
                    },
                ],
            },
            object="LineString",
        )

        auto_schema.registry.register_on_missing(line_string_component)

        multi_line_string_component = ResolvedComponent(
            name="MultiLineString",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Multi-line string",
                "description": "GeoJSON multi-line-string geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.5",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": TYPE_ARRAY,
                                "items": {
                                    "type": TYPE_ARRAY,
                                    "items": point2d_component.ref,
                                },
                            },
                        },
                    },
                ],
            },
            object="MultiLineString",
        )

        auto_schema.registry.register_on_missing(multi_line_string_component)

        polygon_component = ResolvedComponent(
            name="Polygon",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Polygon",
                "description": "GeoJSON polygon geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.6",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": TYPE_ARRAY,
                                "items": {
                                    "type": TYPE_ARRAY,
                                    "items": point2d_component.ref,
                                },
                            },
                        },
                    },
                ],
            },
            object="Polygon",
        )

        auto_schema.registry.register_on_missing(polygon_component)

        multi_polygon_component = ResolvedComponent(
            name="MultiPolygon",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Multi-polygon",
                "description": "GeoJSON multi-polygon geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.7",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": TYPE_ARRAY,
                                "items": {
                                    "type": TYPE_ARRAY,
                                    "items": {
                                        "type": TYPE_ARRAY,
                                        "items": point2d_component.ref,
                                    },
                                },
                            },
                        },
                    },
                ],
            },
            object="MultiPolygon",
        )

        auto_schema.registry.register_on_missing(multi_polygon_component)

        geometry_collection_component = ResolvedComponent(
            name="GeometryCollection",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "Geometry collection",
                "description": "GeoJSON multi-polygon geometry",
                "type": TYPE_OBJECT,
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.8",
                },
                "allOf": [
                    geometry_component.ref,
                    {
                        "type": TYPE_OBJECT,
                        "required": ["geometries"],
                        "properties": {
                            "geometries": {
                                "type": TYPE_ARRAY,
                                "items": geometry_component.ref,
                            },
                        },
                    },
                ],
            },
            object="GeometryCollection",
        )

        auto_schema.registry.register_on_missing(geometry_collection_component)

        root_component = ResolvedComponent(
            name="GeoJSONGeometry",
            type=ResolvedComponent.SCHEMA,
            schema={
                "title": "GeoJSONGeometry",
                "type": TYPE_OBJECT,
                "oneOf": [
                    point_component.ref,
                    multi_point_component.ref,
                    line_string_component.ref,
                    multi_line_string_component.ref,
                    polygon_component.ref,
                    multi_polygon_component.ref,
                    geometry_collection_component.ref,
                ],
                "discriminator": {
                    "propertyName": "type",
                },
            },
            object="GeoJSONGeometry",
        )

        auto_schema.registry.register_on_missing(root_component)

        return root_component.ref
