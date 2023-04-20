from datetime import date

from django.urls import reverse

import pytest

from testapp.models import Group, Record
from testapp.viewsets import GroupViewSet
from vng_api_common.utils import (
    generate_unique_identification,
    get_resources_for_paths,
    get_viewset_for_path,
)


def test_viewset_for_path_no_subpath():
    path = reverse("group-list")

    viewset = get_viewset_for_path(path)

    assert isinstance(viewset, GroupViewSet)


def test_viewset_for_path_with_subpath(script_path):
    """
    Assert that viewset resolution still works when SCRIPT_PATH=/some-prefix is set.

    Upstream reverse proxies ensure that the environment is correctly set, which
    eventually results in django.core.handlers.wsgi.WSGIHandler calling
    :func:`set_script_prefix`. Even with the script prefix, URL resolution needs to
    work correctly.
    """
    path = reverse("group-list")
    assert path.startswith("/some-prefix/")

    viewset = get_viewset_for_path(path)

    assert isinstance(viewset, GroupViewSet)


@pytest.mark.django_db
def test_get_resources_for_paths(django_assert_num_queries):
    group1, group2 = [
        Group.objects.create(),
        Group.objects.create(),
    ]

    paths = [
        f"/api/groups/{group2.pk}",
        f"/api/groups/{group1.pk}",
    ]

    with django_assert_num_queries(1):
        results = get_resources_for_paths(paths)

    assert set(results) == {group1, group2}


@pytest.mark.django_db
def test_get_resources_for_paths_empty(django_assert_num_queries):
    with django_assert_num_queries(0):
        results = get_resources_for_paths([])

    assert results is None


@pytest.mark.django_db
def test_no_resolution():
    group = Group.objects.create()

    paths = [
        f"/api/groups/{group.pk}",
        f"/api/groups/-3",
    ]

    with pytest.raises(RuntimeError):
        get_resources_for_paths(paths)


@pytest.mark.django_db
def test_generate_unique_identification():
    record1 = Record(create_date=date(2023, 3, 3))
    id1 = generate_unique_identification(record1, "create_date")

    assert id1 == "RECORD-2023-0000000001"

    record1.identificatie = id1
    record1.save()
    record2 = Record(create_date=date(2023, 3, 3))
    id2 = generate_unique_identification(record2, "create_date")

    assert id2 == "RECORD-2023-0000000002"
