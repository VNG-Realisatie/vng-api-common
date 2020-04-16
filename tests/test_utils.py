from django.urls import reverse

from testapp.viewsets import GroupViewSet

from vng_api_common.utils import get_viewset_for_path


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
