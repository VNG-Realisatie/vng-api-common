from unittest import mock

from django.utils.translation import gettext as _

import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from vng_api_common.generators import OpenAPISchemaGenerator

pytestmark = pytest.mark.django_db(transaction=True)


def test_schema_root_tags():
    request = APIRequestFactory().get("/api/persons/1")
    request = APIView().initialize_request(request)
    request._request.jwt_auth = mock.Mock()

    generator = OpenAPISchemaGenerator()

    schema = generator.get_schema(request)
    assert "tags" in schema

    description = next(
        tag["description"] for tag in schema["tags"] if tag["name"] == "persons"
    )
    assert description == str(_("This is the global resource description"))
