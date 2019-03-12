from collections import OrderedDict

from drf_yasg import openapi
from drf_yasg.inspectors import FieldInspector, NotHandled
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..geo import DEFAULT_CRS, HEADER_ACCEPT, HEADER_CONTENT

REF_NAME_GEOJSON_GEOMETRY = 'GeoJSONGeometry'


def register_geojson(definitions):
    Geometry = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        title="Geometry",
        description="GeoJSON geometry",
        discriminator='type',
        required=['type'],
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1'),
        properties=OrderedDict((
            ('type', openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=[
                    'Point',
                    'MultiPoint',
                    'LineString',
                    'MultiLineString',
                    'Polygon',
                    'MultiPolygon',
                    'Feature',
                    'FeatureCollection',
                    'GeometryCollection',
                ],
                description="The geometry type"
            )),
        ))
    )
    definitions.set('Geometry', Geometry)

    Point2D = openapi.Schema(
        type=openapi.TYPE_ARRAY,
        title="Point2D",
        description="A 2D point",
        items=openapi.Schema(type=openapi.TYPE_NUMBER),
        maxItems=2,
        minItems=2
    )
    definitions.set('Point2D', Point2D)

    Point = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON point geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.2'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.SchemaRef(definitions, 'Point2D')),
                ))
            )
        ]
    )
    definitions.set('Point', Point)

    MultiPoint = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON multi-point geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.3'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.SchemaRef(definitions, 'Point2D'),
                    )),
                ))
            )
        ]
    )
    definitions.set('MultiPoint', MultiPoint)

    LineString = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON line-string geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.4'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.SchemaRef(definitions, 'Point2D'),
                        minItems=2,
                    )),
                ))
            )
        ]
    )
    definitions.set('LineString', LineString)

    MultiLineString = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON multi-line-string geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.5'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.SchemaRef(definitions, 'Point2D')
                        )
                    )),
                ))
            )
        ]
    )
    definitions.set('MultiLineString', MultiLineString)

    Polygon = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON polygon geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.6'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.SchemaRef(definitions, 'Point2D')
                        )
                    )),
                ))
            )
        ]
    )
    definitions.set('Polygon', Polygon)

    MultiPolygon = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON multi-polygon geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.7'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['coordinates'],
                properties=OrderedDict((
                    ('coordinates', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.SchemaRef(definitions, 'Point2D')
                            )
                        )
                    )),
                ))
            )
        ]
    )
    definitions.set('MultiPolygon', MultiPolygon)

    GeometryCollection = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description="GeoJSON multi-polygon geometry",
        externalDocs=OrderedDict(url='https://tools.ietf.org/html/rfc7946#section-3.1.8'),
        allOf=[
            openapi.SchemaRef(definitions, 'Geometry'),
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['geometries'],
                properties=OrderedDict((
                    ('geometries', openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.SchemaRef(definitions, 'Geometry')
                    )),
                ))
            )
        ]
    )
    definitions.set('GeometryCollection', GeometryCollection)

    GeoJSONGeometry = openapi.Schema(
        title=REF_NAME_GEOJSON_GEOMETRY,
        type=openapi.TYPE_OBJECT,
        oneOf=[
            openapi.SchemaRef(definitions, 'Point'),
            openapi.SchemaRef(definitions, 'MultiPoint'),
            openapi.SchemaRef(definitions, 'LineString'),
            openapi.SchemaRef(definitions, 'MultiLineString'),
            openapi.SchemaRef(definitions, 'Polygon'),
            openapi.SchemaRef(definitions, 'MultiPolygon'),
            openapi.SchemaRef(definitions, 'GeometryCollection'),
        ]
    )
    definitions.set(REF_NAME_GEOJSON_GEOMETRY, GeoJSONGeometry)


class GeometryFieldInspector(FieldInspector):

    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        if not isinstance(field, GeometryField):
            return NotHandled

        definitions = self.components.with_scope(openapi.SCHEMA_DEFINITIONS)

        if not definitions.has('Geometry'):
            register_geojson(definitions)

        return openapi.SchemaRef(definitions, REF_NAME_GEOJSON_GEOMETRY)

    def has_geo_fields(self, serializer) -> bool:
        """
        Check if any of the serializer fields are a GeometryField.

        If the serializer has nested serializers, a depth-first search is done
        to check if the nested serializers has `GeometryField`\ s.
        """
        for field in serializer.fields.values():
            if isinstance(field, serializers.Serializer):
                has_nested_geo_fields = self.probe_inspectors(
                    self.field_inspectors, 'has_geo_fields',
                    field, {'field_inspectors': self.field_inspectors}
                )
                if has_nested_geo_fields:
                    return True

            elif isinstance(field, (serializers.ListSerializer, serializers.ListField)):
                field = field.child

            if isinstance(field, GeometryField):
                return True

        return False

    def get_request_header_parameters(self, serializer):
        if not self.has_geo_fields(serializer):
            return []

        if self.method == 'DELETE':
            return []

        # see also http://lyzidiamond.com/posts/4326-vs-3857 for difference
        # between coordinate system and projected coordinate system
        return [openapi.Parameter(
            name=HEADER_ACCEPT,
            type=openapi.TYPE_STRING,
            in_=openapi.IN_HEADER,
            required=True,
            description="Het gewenste 'Coordinate Reference System' (CRS) van de "
                        "geometrie in het antwoord (response body). Volgens de "
                        "GeoJSON spec is WGS84 de default (EPSG:4326 is "
                        "hetzelfde als WGS84).",
            enum=[DEFAULT_CRS]
        ), openapi.Parameter(
            name=HEADER_CONTENT,
            type=openapi.TYPE_STRING,
            in_=openapi.IN_HEADER,
            required=True,
            description="Het 'Coordinate Reference System' (CRS) van de "
                        "geometrie in de vraag (request body). Volgens de "
                        "GeoJSON spec is WGS84 de default (EPSG:4326 is "
                        "hetzelfde als WGS84).",
            enum=[DEFAULT_CRS]
        )]

    def get_response_headers(self, serializer, status=None):
        if not self.has_geo_fields(serializer):
            return None

        if int(status) != 200:
            return None

        return OrderedDict((
            (HEADER_CONTENT, openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=[DEFAULT_CRS],
                description="Het 'Coordinate Reference System' (CRS) van de "
                            "antwoorddata. Volgens de GeoJSON spec is WGS84 de "
                            "default (EPSG:4326 is hetzelfde als WGS84).",
            )),
        ))
