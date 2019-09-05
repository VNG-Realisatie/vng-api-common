import pytest
from rest_framework import status
from rest_framework.reverse import reverse

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
