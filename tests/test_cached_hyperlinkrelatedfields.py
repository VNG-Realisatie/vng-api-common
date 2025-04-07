from unittest.mock import patch

from django.urls import reverse

import pytest
from rest_framework.reverse import reverse

from testapp.factories import GroupFactory, PersonFactory


@pytest.mark.django_db
def test_cached_hyperlinkedrelatedfield(api_client):
    """
    Caching is applied to the base URI for each view in CachedHyperlinkedRelatedField,
    but this cache must be only be applied within the same requests, to ensure that
    requests with different HTTP_HOSTs show the correct domain in their responses
    """
    group = GroupFactory.create(name="group1")
    person = PersonFactory.create(
        name="John Doe", address_street="Foo", address_number="1", group=group
    )

    response = api_client.get(reverse("person-detail", kwargs={"pk": person.pk}))

    expected = {
        "url": f"http://testserver{reverse('person-detail', kwargs={'pk': person.pk})}",
        "address": {"street": "Foo", "number": "1"},
        "name": "John Doe",
        "group_name": "group1",
        "group_url": f"http://testserver{reverse('group-detail', kwargs={'pk': group.pk})}",
    }

    assert response.data == expected

    response = api_client.get(
        reverse("person-detail", kwargs={"pk": person.pk}), HTTP_HOST="different.local"
    )

    expected = {
        "url": f"http://different.local{reverse('person-detail', kwargs={'pk': person.pk})}",
        "address": {"street": "Foo", "number": "1"},
        "name": "John Doe",
        "group_name": "group1",
        "group_url": f"http://different.local{reverse('group-detail', kwargs={'pk': group.pk})}",
    }

    assert response.data == expected


@pytest.mark.django_db
def test_cached_nested_hyperlinkedrelatedfield(api_client):
    """
    Caching is applied to the base URI for each view in CachedNestedHyperlinkedRelatedField,
    but this cache must be only be applied within the same requests, to ensure that
    requests with different HTTP_HOSTs show the correct domain in their responses
    """
    group = GroupFactory.create(name="group1")
    person1 = PersonFactory.create(
        name="John Doe", address_street="Foo", address_number="1", group=group
    )
    person2 = PersonFactory.create(
        name="Jane Doe", address_street="Bar", address_number="2", group=group
    )

    with patch("rest_framework.relations.reverse", side_effect=reverse) as mock_reverse:
        response = api_client.get(reverse("group-detail", kwargs={"pk": group.pk}))

        # Without caching 6 calls would be made to reverse, caching reduces this to 3
        # (one for each view)
        assert mock_reverse.call_count == 3
        assert mock_reverse.call_args_list[0].args == ("person-detail",)
        assert mock_reverse.call_args_list[1].args == ("group-detail",)
        assert mock_reverse.call_args_list[2].args == ("nested-person-detail",)

    expected = {
        "persons": [
            {
                "url": f"http://testserver{reverse('person-detail', kwargs={'pk': person1.pk})}",
                "address": {"street": "Foo", "number": "1"},
                "name": "John Doe",
                "group_name": "group1",
                "group_url": f"http://testserver{reverse('group-detail', kwargs={'pk': group.pk})}",
            },
            {
                "url": f"http://testserver{reverse('person-detail', kwargs={'pk': person2.pk})}",
                "address": {"street": "Bar", "number": "2"},
                "name": "Jane Doe",
                "group_name": "group1",
                "group_url": f"http://testserver{reverse('group-detail', kwargs={'pk': group.pk})}",
            },
        ],
        "nested_persons": [
            f"http://testserver{reverse('nested-person-detail', kwargs={'group_pk': group.pk, 'pk': person1.pk})}",
            f"http://testserver{reverse('nested-person-detail', kwargs={'group_pk': group.pk, 'pk': person2.pk})}",
        ],
    }

    assert response.data == expected

    response = api_client.get(
        reverse("group-detail", kwargs={"pk": group.pk}), HTTP_HOST="different.local"
    )

    expected = {
        "persons": [
            {
                "url": f"http://different.local{reverse('person-detail', kwargs={'pk': person1.pk})}",
                "address": {"street": "Foo", "number": "1"},
                "name": "John Doe",
                "group_name": "group1",
                "group_url": f"http://different.local{reverse('group-detail', kwargs={'pk': group.pk})}",
            },
            {
                "url": f"http://different.local{reverse('person-detail', kwargs={'pk': person2.pk})}",
                "address": {"street": "Bar", "number": "2"},
                "name": "Jane Doe",
                "group_name": "group1",
                "group_url": f"http://different.local{reverse('group-detail', kwargs={'pk': group.pk})}",
            },
        ],
        "nested_persons": [
            f"http://different.local{reverse('nested-person-detail', kwargs={'group_pk': group.pk, 'pk': person1.pk})}",
            f"http://different.local{reverse('nested-person-detail', kwargs={'group_pk': group.pk, 'pk': person2.pk})}",
        ],
    }

    assert response.data == expected
