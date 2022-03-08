from django.urls import reverse

import pytest

from testapp.models import Group
from testapp.viewsets import GroupViewSet
from vng_api_common.utils import get_resources_for_paths, get_viewset_for_path


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
