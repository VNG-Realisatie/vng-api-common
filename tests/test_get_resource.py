from django.core.exceptions import ObjectDoesNotExist

import pytest

from vng_api_common.utils import NotAViewSet, get_resource_for_path


@pytest.mark.parametrize(
    "path,exc", (("/", NotAViewSet), ("/foo/", ObjectDoesNotExist))
)
def test_get_resource_for_path_with_trailing_slash(path, exc):
    with pytest.raises(exc):
        get_resource_for_path(path)
