from unittest.mock import patch

from django.db import transaction

import pytest
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status, viewsets
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from testapp.factories import GroupFactory, HobbyFactory, PersonFactory
from testapp.models import Hobby, Person
from testapp.serializers import HobbySerializer
from testapp.viewsets import PersonViewSet
from vng_api_common.caching.decorators import conditional_retrieve
from vng_api_common.extensions.utils import get_cache_headers

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.django_db(transaction=False)
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

    assert any((True for header in headers if header.name == "ETag"))


@pytest.mark.django_db(transaction=False)
def test_related_resource_changes_recalculate_etag1(django_capture_on_commit_callbacks):
    # Assert that resources references in the serializer trigger ETag recalculates, while
    # resources not referenced don't.
    hobbies = [
        HobbyFactory.create(name="playing guitar"),
        HobbyFactory.create(name="playing synths"),
    ]
    person = PersonFactory.create(
        name="Jon Carpenter",
        address_street="Synthwave",
        address_number="101",
        # included in serializer, however this is through a serializer method field and thus
        # explicitly declared. See the next test case for implicit relation following from
        # the serializer fields.
        group=GroupFactory.create(name="Brut"),
    )
    person.hobbies.set(hobbies)  # not included in serializer
    person.calculate_etag_value()

    # discard any scheduled callback handlers from test set up
    transaction.get_connection().run_on_commit = []

    assert person._etag, "No ETag value calculated"
    initial_etag_value = person._etag

    # start test 1 - changing the hobbies should not result in changed etags
    with django_capture_on_commit_callbacks(execute=True):
        person.hobbies.clear()

    person.refresh_from_db()

    assert person._etag == initial_etag_value

    # start test 2 - changing the group does affect the serializer output and thus the etag value
    # discard any scheduled callback handlers from test set up
    transaction.get_connection().run_on_commit = []
    with django_capture_on_commit_callbacks(execute=True):
        person.group.name = "DWTD"
        person.group.save()

    person.refresh_from_db()

    assert person._etag, "ETag should have been set"
    assert person._etag != initial_etag_value, "ETag value should have been changed"


@pytest.mark.django_db(transaction=False)
def test_related_resource_changes_recalculate_etag2(django_capture_on_commit_callbacks):
    # has a simple (reverse) m2m to Person
    person = PersonFactory.create()
    hobby = HobbyFactory.create()
    hobby.calculate_etag_value()

    assert hobby._etag, "No ETag value calculated"
    initial_etag_value = hobby._etag

    # now, change the related people resource to the hobby, which should trigger a
    # re-calculate
    # discard any scheduled callback handlers from test set up
    transaction.get_connection().run_on_commit = []
    with django_capture_on_commit_callbacks(execute=True):
        person.hobbies.add(hobby)

    hobby.refresh_from_db()
    assert hobby._etag, "ETag should have been set"
    assert hobby._etag != initial_etag_value, "ETag value should have been changed"


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


@pytest.mark.django_db(transaction=False)
def test_etag_updates_deduped(django_capture_on_commit_callbacks):
    with patch(
        "testapp.models.Person.calculate_etag_value"
    ) as mock_calculate_etag_value:
        with django_capture_on_commit_callbacks(execute=True):
            # one post_save
            person = PersonFactory.create()
            # second post_save
            person.save()

    assert mock_calculate_etag_value.call_count == 1


class DynamicSerializerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()

    def get_serializer(self, *args, **kwargs):
        return HobbySerializer()


def test_dynamic_serializer():
    REPLACEMENT_REGISTRY = {}
    with patch(
        "vng_api_common.caching.registry.DEPENDENCY_REGISTRY", new=REPLACEMENT_REGISTRY
    ):
        conditional_retrieve()(DynamicSerializerViewSet)

    assert Person in REPLACEMENT_REGISTRY


def test_etag_object_cascading_delete():
    group = GroupFactory.create()
    PersonFactory.create(group=group)

    group.delete()
