from unittest import mock

import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from testapp.viewsets import PersonViewSet
from vng_api_common.generators import OpenAPISchemaGenerator
from vng_api_common.utils import get_view_summary

pytestmark = pytest.mark.django_db(transaction=True)


def test_schema_root_tags():
    request = APIRequestFactory().get("/api/persons/1")
    request = APIView().initialize_request(request)
    request._request.jwt_auth = mock.Mock()

    generator = OpenAPISchemaGenerator()

    schema = generator.get_schema(request)
    assert "tags" in schema

    summary = next(
        tag["description"] for tag in schema["tags"] if tag["name"] == "persons"
    )
    assert summary == "Summary\n\nMore summary"


def test_view_summary():
    summary = get_view_summary(PersonViewSet)

    assert summary == "Summary\n\nMore summary"
