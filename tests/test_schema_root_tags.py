import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from vng_api_common.generators import OpenAPISchemaGenerator


@pytest.fixture(scope="module")
def schema():
    """Here be isolation dragons 🐲
    Caching of resolvers, callbacks, urlconfs is not clean
    with willy-nilly mutation of attributes everywhere.

    Creating this fixture in module scope is probably hiding bugs and issues
    """

    generator = OpenAPISchemaGenerator()
    request = APIRequestFactory().get("/api/persons/1")

    request = APIView().initialize_request(request)

    return generator.get_schema(request)


def test_schema_root_tags(schema):
    assert "tags" in schema
    tags = schema["tags"]
    persons_tag = [t for t in tags if t["name"] == "persons"]
    assert len(persons_tag) == 1


def test_schema_root_tags_contains_tags_from_settings(schema):
    # not using override_settings / settings fixture on purpose
    assert "tags" in schema
    tags = schema["tags"]
    moloko_tag = [t for t in tags if t["name"] == "moloko_milk_bar"][0]
    assert moloko_tag == {
        "name": "moloko_milk_bar",
        "description": "Global tag description via settings",
    }
