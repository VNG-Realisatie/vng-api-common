import logging

from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema, OpenApiTypes
from drf_spectacular.plumbing import ResolvedComponent, build_basic_type


logger = logging.getLogger(__name__)

TYPES_MAP = {
    str: OpenApiTypes.STR,
    int: OpenApiTypes.INT,
    bool: OpenApiTypes.BOOL,
}


class ReadOnlyFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.serializers.ReadOnlyField"

    def map_serializer_field(self, auto_schema: AutoSchema, direction):
        prop = getattr(self.target.parent.Meta.model, self.target.source)
        if not isinstance(prop, property):
            return super().map_serializer_field(auto_schema, direction)

        return_type = prop.fget.__annotations__.get("return")
        if return_type is None:
            logger.debug(
                "Missing return type annotation for prop %s on model %s",
                self.field.source,
                self.field.parent.Meta.model,
            )
            return super().map_serializer_field(auto_schema, direction)

        type_ = TYPES_MAP.get(return_type)
        if type_ is None:
            logger.debug("Missing type mapping for %r", return_type)

        return build_basic_type(type_ or OpenApiTypes.STR)


class HyperlinkedRelatedFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "vng_api_common.serializers.LengthHyperlinkedRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema: AutoSchema, direction):
        return {
            "type": "string",
            "format": "uri",
            "minLength": self.target.min_length,
            "maxLength": self.target.max_length,
            "description": self.target.help_text or "",
        }


class HyperlinkedIdentityFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework.serializers.HyperlinkedIdentityField"

    def map_serializer_field(self, auto_schema: AutoSchema, direction):
        return {
            "type": "string",
            "format": "uri",
            "minLength": 1,
            "maxLength": 1000,
            "description": _(
                "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
            ),
        }


class GeometryFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework_gis.fields.GeometryField"
    match_subclasses = True
    priority = 1

    def get_name(self):
        return "GeoJSONGeometry"

    def map_serializer_field(self, auto_schema, direction):
        geometry = ResolvedComponent(
            name="Geometry",
            type=ResolvedComponent.SCHEMA,
            object="Geometry",
            schema={
                "type": "object",
                "title": "Geometry",
                "description": "GeoJSON geometry",
                "required": ["type"],
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1"
                },
                "properties": {
                    "type": {
                        "type": "string",
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
        )
        point_2d = ResolvedComponent(
            name="Point2D",
            type=ResolvedComponent.SCHEMA,
            object="Point2D",
            schema={
                "type": "array",
                "title": "Point2D",
                "description": "A 2D point",
                "items": {"type": "number"},
                "maxItems": 2,
                "minItems": 2,
            },
        )
        point = ResolvedComponent(
            name="Point",
            type=ResolvedComponent.SCHEMA,
            object="Point",
            schema={
                "type": "object",
                "description": "GeoJSON point geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.2"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {"coordinates": point_2d.ref},
                    },
                ],
            },
        )

        multi_point = ResolvedComponent(
            name="MultiPoint",
            type=ResolvedComponent.SCHEMA,
            object="MultiPoint",
            schema={
                "type": "object",
                "description": "GeoJSON multi-point geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.3"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {"type": "array", "items": point_2d.ref}
                        },
                    },
                ],
            },
        )

        line_string = ResolvedComponent(
            name="LineString",
            type=ResolvedComponent.SCHEMA,
            object="LineString",
            schema={
                "type": "object",
                "description": "GeoJSON line-string geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.4"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": point_2d.ref,
                                "minItems": 2,
                            }
                        },
                    },
                ],
            },
        )

        multi_line_string = ResolvedComponent(
            name="MultiLineString",
            type=ResolvedComponent.SCHEMA,
            object="MultiLineString",
            schema={
                "type": "object",
                "description": "GeoJSON multi-line-string geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.5"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": point_2d.ref,
                                },
                            }
                        },
                    },
                ],
            },
        )

        polygon = ResolvedComponent(
            name="Polygon",
            type=ResolvedComponent.SCHEMA,
            object="Polygon",
            schema={
                "type": "object",
                "description": "GeoJSON polygon geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.6"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": point_2d.ref,
                                },
                            }
                        },
                    },
                ],
            },
        )

        multi_polygon = ResolvedComponent(
            name="MultiPolygon",
            type=ResolvedComponent.SCHEMA,
            object="MultiPolygon",
            schema={
                "type": "object",
                "description": "GeoJSON multi-polygon geometry",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.7"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["coordinates"],
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": point_2d.ref,
                                    },
                                },
                            }
                        },
                    },
                ],
            },
        )

        geometry_collection = ResolvedComponent(
            name="GeometryCollection",
            type=ResolvedComponent.SCHEMA,
            object="GeometryCollection",
            schema={
                "type": "object",
                "description": "GeoJSON geometry collection",
                "externalDocs": {
                    "url": "https://tools.ietf.org/html/rfc7946#section-3.1.8"
                },
                "allOf": [
                    geometry.ref,
                    {
                        "type": "object",
                        "required": ["geometries"],
                        "properties": {
                            "geometries": {"type": "array", "items": geometry.ref}
                        },
                    },
                ],
            },
        )

        for component in [
            geometry,
            point_2d,
            point,
            multi_point,
            line_string,
            multi_line_string,
            polygon,
            multi_polygon,
            geometry_collection,
        ]:
            auto_schema.registry.register_on_missing(component)

        return {
            "title": "GeoJSONGeometry",
            "type": "object",
            "oneOf": [
                point.ref,
                multi_point.ref,
                line_string.ref,
                multi_line_string.ref,
                polygon.ref,
                multi_polygon.ref,
                geometry_collection.ref,
            ],
            "discriminator": {
                "propertyName": "type",
            },
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
