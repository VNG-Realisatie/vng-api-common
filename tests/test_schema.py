from django.urls import include, path

from testapp.viewsets import GeometryViewSet, MediaFileViewSet
from tests import generate_schema
from vng_api_common import routers

app_name = "schema"

router = routers.DefaultRouter(trailing_slash=False)
router.register("base64", MediaFileViewSet, basename="schema_base64")
router.register("geo", GeometryViewSet, basename="schema_geometry")

urlpatterns = [
    path("api/", include(router.urls)),
]


def _generate_schema():
    return generate_schema(urlpatterns)


def test_schema_root_tags():
    schema = _generate_schema()

    assert schema["paths"]["/api/base64"]["post"]["tags"] == ["api"]
    assert schema["paths"]["/api/base64"]["get"]["tags"] == ["api"]

    assert schema["paths"]["/api/base64/{id}"]["get"]["tags"] == ["api"]
    assert schema["paths"]["/api/base64/{id}"]["put"]["tags"] == ["api"]
    assert schema["paths"]["/api/base64/{id}"]["patch"]["tags"] == ["api"]
    assert schema["paths"]["/api/base64/{id}"]["delete"]["tags"] == ["api"]

    # global tag from settings
    assert {
        "name": "moloko_milk_bar",
        "description": "Global tag description via settings",
    } in schema["tags"]


def test_error_response():
    schema = _generate_schema()

    status_code_with_schema = {
        "400": "#/components/schemas/ValidatieFout",
        "401": "#/components/schemas/Fout",
        "403": "#/components/schemas/Fout",
        "406": "#/components/schemas/Fout",
        "409": "#/components/schemas/Fout",
        "410": "#/components/schemas/Fout",
        "412": "#/components/schemas/Fout",
        "415": "#/components/schemas/Fout",
        "429": "#/components/schemas/Fout",
        "500": "#/components/schemas/Fout",
    }

    for status_code, ref_schema in status_code_with_schema.items():
        for method in ["get", "post"]:
            assert schema["paths"]["/api/geo"][method]["responses"][status_code][
                "content"
            ] == {
                "application/problem+json": {
                    "schema": {"$ref": ref_schema},
                }
            }

    assert schema["components"]["schemas"]["Fout"] == {
        "type": "object",
        "description": "Formaat van HTTP 4xx en 5xx fouten.",
        "properties": {
            "type": {
                "type": "string",
                "description": "URI referentie naar het type fout, bedoeld voor developers",
            },
            "code": {
                "type": "string",
                "description": "Systeemcode die het type fout aangeeft",
            },
            "title": {
                "type": "string",
                "description": "Generieke titel voor het type fout",
            },
            "status": {"type": "integer", "description": "De HTTP status code"},
            "detail": {
                "type": "string",
                "description": "Extra informatie bij de fout, indien beschikbaar",
            },
            "instance": {
                "type": "string",
                "description": "URI met referentie naar dit specifiek voorkomen van de fout. Deze kan gebruikt worden in combinatie met server logs, bijvoorbeeld.",
            },
        },
        "required": ["code", "detail", "instance", "status", "title"],
    }

    assert schema["components"]["schemas"]["FieldValidationError"] == {
        "type": "object",
        "description": "Formaat van validatiefouten.",
        "properties": {
            "name": {
                "type": "string",
                "description": "Naam van het veld met ongeldige gegevens",
            },
            "code": {
                "type": "string",
                "description": "Systeemcode die het type fout aangeeft",
            },
            "reason": {
                "type": "string",
                "description": "Uitleg wat er precies fout is met de gegevens",
            },
        },
        "required": ["code", "name", "reason"],
    }


def test_operation_id():
    schema = _generate_schema()

    assert (
        schema["paths"]["/api/base64/{id}"]["get"]["operationId"]
        == "schema_base64_read"
    )
    assert (
        schema["paths"]["/api/base64"]["post"]["operationId"] == "schema_base64_create"
    )
    assert (
        schema["paths"]["/api/base64/{id}"]["put"]["operationId"]
        == "schema_base64_update"
    )
    assert (
        schema["paths"]["/api/base64/{id}"]["patch"]["operationId"]
        == "schema_base64_partial_update"
    )
    assert (
        schema["paths"]["/api/base64/{id}"]["delete"]["operationId"]
        == "schema_base64_delete"
    )


def test_content_type_headers():
    schema = _generate_schema()

    assert {
        "in": "header",
        "name": "Content-Type",
        "schema": {"type": "string", "enum": ["application/json"]},
        "description": "Content type of the request body.",
        "required": True,
    } in schema["paths"]["/api/base64"]["post"]["parameters"]

    assert {
        "in": "path",
        "name": "id",
        "schema": {"type": "integer"},
        "description": "A unique integer value identifying this media file model.",
        "required": True,
    } in schema["paths"]["/api/base64/{id}"]["put"]["parameters"]
    assert {
        "in": "path",
        "name": "id",
        "schema": {"type": "integer"},
        "description": "A unique integer value identifying this media file model.",
        "required": True,
    } in schema["paths"]["/api/base64/{id}"]["patch"]["parameters"]


def test_geo_headers():
    schema = _generate_schema()

    # headers
    assert schema["paths"]["/api/geo"]["get"]["responses"]["200"]["headers"][
        "Content-Crs"
    ] == {
        "schema": {"type": "string", "enum": ["EPSG:4326"]},
        "description": "The 'Coordinate Reference System' (CRS) of the request data. According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 is the same as WGS84).",
        "required": True,
    }

    # parameters
    for method, path in {
        "post": "/api/geo",
        "put": "/api/geo/{id}",
        "patch": "/api/geo/{id}",
    }.items():
        assert {
            "in": "header",
            "name": "Accept-Crs",
            "schema": {"type": "string", "enum": ["EPSG:4326"]},
            "description": "The desired 'Coordinate Reference System' (CRS) of the response data. According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 is the same as WGS84).",
        } in schema["paths"][path][method]["parameters"]
        assert {
            "in": "header",
            "name": "Content-Crs",
            "schema": {"type": "string", "enum": ["EPSG:4326"]},
            "description": "The 'Coordinate Reference System' (CRS) of the request data. According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 is the same as WGS84).",
            "required": True,
        } in schema["paths"][path][method]["parameters"]

    assert {
        "in": "header",
        "name": "Accept-Crs",
        "schema": {"type": "string", "enum": ["EPSG:4326"]},
        "description": "The desired 'Coordinate Reference System' (CRS) of the response data. According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 is the same as WGS84).",
    } in schema["paths"]["/api/geo/{id}"]["put"]["parameters"]


def test_version_headers():
    schema = _generate_schema()

    for status_code in [
        "400",
        "401",
        "403",
        "406",
        "409",
        "410",
        "412",
        "415",
        "429",
        "500",
    ]:
        for method in ["get", "post"]:
            assert schema["paths"]["/api/geo"][method]["responses"][status_code][
                "headers"
            ]["API-version"] == {
                "schema": {"type": "string"},
                "description": "Geeft een specifieke API-versie aan in de context van een specifieke aanroep. Voorbeeld: 1.2.1.",
            }


def test_location_headers():
    schema = _generate_schema()
    assert schema["paths"]["/api/base64"]["post"]["responses"]["201"]["headers"][
        "Location"
    ] == {
        "schema": {"type": "string", "format": "uri"},
        "description": "URL waar de resource leeft.",
    }
