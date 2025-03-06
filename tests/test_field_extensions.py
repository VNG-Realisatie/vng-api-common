from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, viewsets

from testapp.models import FkModel, Poly
from testapp.viewsets import GeometryViewSet, MediaFileViewSet, PolyViewSet
from tests import generate_schema
from vng_api_common import routers
from vng_api_common.serializers import LengthHyperlinkedRelatedField


class LengthHyperLinkedSerializer(serializers.ModelSerializer):
    poly = LengthHyperlinkedRelatedField(
        view_name="field_extention_poly-detail",
        lookup_field="uuid",
        queryset=Poly.objects,
        min_length=20,
        max_length=500,
        help_text=_("test123"),
    )

    class Meta:
        model = FkModel
        fields = ("poly",)


class HyperlinkedIdentityFieldSerializer(serializers.ModelSerializer):
    poly = serializers.HyperlinkedIdentityField(
        view_name="poly-detail",
        lookup_field="uuid",
    )

    class Meta:
        model = FkModel
        fields = ("poly",)


class LengthHyperLinkedViewSet(viewsets.ModelViewSet):
    queryset = Poly.objects.all()
    serializer_class = LengthHyperLinkedSerializer


class HyperlinkedIdentityViewSet(viewsets.ModelViewSet):
    queryset = FkModel.objects.all()
    serializer_class = HyperlinkedIdentityFieldSerializer


app_name = "field_extensions"

router = routers.DefaultRouter(trailing_slash=False)
router.register("base64", MediaFileViewSet, basename="field_extensions_base64")
router.register("geo", GeometryViewSet, basename="field_extensions_geometry")
router.register("length", LengthHyperLinkedViewSet, basename="field_extensions_length")
router.register(
    "identity", HyperlinkedIdentityViewSet, basename="field_extensions_identity"
)
router.register("poly", PolyViewSet, basename="field_extensions_poly")

urlpatterns = [
    path("api/", include(router.urls)),
]


def _generate_schema():
    return generate_schema(urlpatterns)


def test_base64():
    schema = _generate_schema()
    path = schema["components"]["schemas"]

    assert path["MediaFileModel"]["properties"]["file"] == {
        "type": "string",
        "format": "uri",
        "description": "Download URL of the binary content.",
        "nullable": True,
    }

    assert path["PatchedMediaFileModel"]["properties"]["file"] == {
        "type": "string",
        "format": "byte",
        "description": "Base64 encoded binary content.",
        "nullable": True,
    }


def test_hyper_link_related_field():
    schema = _generate_schema()

    assert schema["components"]["schemas"]["LengthHyperLinked"]["properties"][
        "poly"
    ] == {
        "type": "string",
        "format": "uri",
        "minLength": 20,
        "maxLength": 500,
        "description": "test123",
    }


def test_hyper_link_identity_field():
    schema = _generate_schema()

    assert schema["components"]["schemas"]["HyperlinkedIdentityField"]["properties"][
        "poly"
    ] == {
        "type": "string",
        "format": "uri",
        "minLength": 1,
        "maxLength": 1000,
        "description": "URL reference to this object. This is the unique identification and location of this object.",
        "readOnly": True,
    }


def test_geometry_field():
    schema = _generate_schema()
    schemas = schema["components"]["schemas"]

    assert schemas["GeoJSONGeometry"] == {
        "title": "GeoJSONGeometry",
        "type": "object",
        "oneOf": [
            {"$ref": "#/components/schemas/Point"},
            {"$ref": "#/components/schemas/MultiPoint"},
            {"$ref": "#/components/schemas/LineString"},
            {"$ref": "#/components/schemas/MultiLineString"},
            {"$ref": "#/components/schemas/Polygon"},
            {"$ref": "#/components/schemas/MultiPolygon"},
            {"$ref": "#/components/schemas/GeometryCollection"},
        ],
        "discriminator": {"propertyName": "type"},
    }

    assert schemas["Geometry"] == {
        "type": "object",
        "title": "Geometry",
        "description": "GeoJSON geometry",
        "required": ["type"],
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1"},
        "properties": {
            "type": {
                "allOf": [{"$ref": "#/components/schemas/TypeEnum"}],
                "description": "The geometry type",
            },
        },
    }

    assert schemas["GeometryCollection"] == {
        "type": "object",
        "description": "GeoJSON geometry collection",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.8"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["geometries"],
                "properties": {
                    "geometries": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Geometry"},
                    },
                },
            },
        ],
    }

    assert schemas["LineString"] == {
        "type": "object",
        "description": "GeoJSON line-string geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.4"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Point2D"},
                        "minItems": 2,
                    },
                },
            },
        ],
    }

    assert schemas["MultiLineString"] == {
        "type": "object",
        "description": "GeoJSON multi-line-string geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.5"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Point2D"},
                        },
                    },
                },
            },
        ],
    }

    assert schemas["MultiPoint"] == {
        "type": "object",
        "description": "GeoJSON multi-point geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.3"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Point2D"},
                    },
                },
            },
        ],
    }

    assert schemas["MultiPolygon"] == {
        "type": "object",
        "description": "GeoJSON multi-polygon geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.7"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
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
                                "items": {
                                    "$ref": "#/components/schemas/Point2D",
                                },
                            },
                        },
                    },
                },
            },
        ],
    }

    assert schemas["Point"] == {
        "type": "object",
        "description": "GeoJSON point geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.2"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {"$ref": "#/components/schemas/Point2D"},
                },
            },
        ],
    }

    assert schemas["Point2D"] == {
        "type": "array",
        "title": "Point2D",
        "description": "A 2D point",
        "items": {"type": "number"},
        "maxItems": 2,
        "minItems": 2,
    }

    assert schemas["Polygon"] == {
        "type": "object",
        "description": "GeoJSON polygon geometry",
        "externalDocs": {"url": "https://tools.ietf.org/html/rfc7946#section-3.1.6"},
        "allOf": [
            {"$ref": "#/components/schemas/Geometry"},
            {
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Point2D"},
                        },
                    },
                },
            },
        ],
    }
