import pytest
from drf_yasg import openapi
from drf_yasg.generators import SchemaGenerator
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from testapp.viewsets import PersonViewSet

from vng_api_common.inspectors.cache import get_cache_headers

pytestmark = pytest.mark.django_db(transaction=True)


def test_etag_header_present(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    response = api_client.get(path)

    person.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert "ETag" in response
    assert response["ETag"] == f'"{person._etag}"'


def test_304_on_cached_resource(api_client, person):
    person.calculate_etag_value()
    path = reverse("person-detail", kwargs={"pk": person.pk})

    response = api_client.get(path, HTTP_IF_NONE_MATCH=f'"{person._etag}"')

    assert response.status_code == status.HTTP_304_NOT_MODIFIED
    assert "Etag" in response


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


def test_etag_changes_m2m_changes_forward(api_client, hobby, person):
    # ensure etags are calculted
    person_path = reverse("person-detail", kwargs={"pk": person.pk})
    hobby_path = reverse("hobby-detail", kwargs={"pk": hobby.pk})
    person_response = api_client.get(person_path)
    hobby_response = api_client.get(hobby_path)
    person.refresh_from_db()
    hobby.refresh_from_db()

    # change the m2m, in the forward direction
    person.hobbies.add(hobby)

    # compare the new ETags
    person_response2 = api_client.get(person_path)
    hobby_response2 = api_client.get(hobby_path)
    assert person_response["ETag"]
    assert person_response["ETag"] != '""'
    assert person_response["ETag"] == person_response2["ETag"]

    assert hobby_response["ETag"]
    assert hobby_response["ETag"] != '""'
    assert hobby_response["ETag"] != hobby_response2["ETag"]


def test_etag_changes_m2m_changes_reverse(api_client, hobby, person):
    path = reverse("hobby-detail", kwargs={"pk": hobby.pk})
    response = api_client.get(path)
    hobby.refresh_from_db()
    assert "ETag" in response
    etag = response["ETag"]

    # change the m2m - reverse direction
    hobby.people.add(person)

    response2 = api_client.get(path)
    assert "ETag" in response2
    assert response2["ETag"]
    assert response2["ETag"] != '""'
    assert response2["ETag"] != etag


def test_remove_m2m(api_client, person, hobby):
    hobby_path = reverse("hobby-detail", kwargs={"pk": hobby.pk})
    person.hobbies.add(hobby)

    etag = api_client.get(hobby_path)["ETag"]
    hobby.refresh_from_db()
    assert etag
    assert etag != '""'

    # this changes the output of the hobby resource
    person.hobbies.remove(hobby)

    new_etag = api_client.get(hobby_path)["ETag"]
    assert new_etag
    assert new_etag != '""'
    assert new_etag != etag


def test_remove_m2m_reverse(api_client, person, hobby):
    hobby_path = reverse("hobby-detail", kwargs={"pk": hobby.pk})
    person.hobbies.add(hobby)

    etag = api_client.get(hobby_path)["ETag"]
    hobby.refresh_from_db()
    assert etag
    assert etag != '""'

    # this changes the output of the hobby resource
    hobby.people.remove(person)

    new_etag = api_client.get(hobby_path)["ETag"]
    assert new_etag
    assert new_etag != '""'
    assert new_etag != etag


def test_related_object_changes_etag(api_client, person, group):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    # set up group object for person
    person.group = group
    person.save()

    etag1 = api_client.get(path)["ETag"]
    person.refresh_from_db()
    assert etag1
    assert etag1 != '""'

    # change the group name, should change the ETag
    group.name = "bar"
    group.save()

    etag2 = api_client.get(path)["ETag"]

    assert etag2
    assert etag2 != '""'
    assert etag2 != etag1


def test_etag_clearing_without_raw_key_in_kwargs(person):
    person.delete()


def test_delete_resource_after_get(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})

    api_client.get(path)

    person.refresh_from_db()
    person.delete()


def test_fetching_cache_enabled_deleted_resource_404s(api_client, person):
    path = reverse("person-detail", kwargs={"pk": person.pk})
    person.delete()

    response = api_client.get(path)

    assert response.status_code == 404
