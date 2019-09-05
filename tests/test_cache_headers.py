import pytest
from drf_yasg import openapi
from drf_yasg.generators import SchemaGenerator
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from testapp.viewsets import PersonViewSet

from vng_api_common.inspectors.cache import get_cache_headers

pytestmark = pytest.mark.django_db


def test_etag_header_present(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK
    assert "ETag" in response
    assert response["ETag"] == f'"{person._etag}"'


def test_304_on_cached_resource(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    response = api_client.get(path, HTTP_IF_NONE_MATCH=f'"{person._etag}"')

    assert response.status_code == status.HTTP_304_NOT_MODIFIED


def test_200_on_stale_resource(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    response = api_client.get(path, HTTP_IF_NONE_MATCH='"stale"')

    assert response.status_code == status.HTTP_200_OK


def test_cache_headers_detected():
    request = APIRequestFactory().get("/api/persons/1")
    request = APIView().initialize_request(request)
    callback = PersonViewSet.as_view({"get": "retrieve"}, detail=True)
    generator = SchemaGenerator()

    view = generator.create_view(callback, "GET", request=request)

    headers = get_cache_headers(view)

    assert "ETag" in headers
    assert isinstance(headers["ETag"], openapi.Schema)
