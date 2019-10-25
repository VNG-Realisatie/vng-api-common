from django.core.exceptions import ObjectDoesNotExist, ValidationError

import pytest
from testapp.models import Person

from vng_api_common.utils import get_resource_for_path


def test_get_resource_for_path_with_trailing_slash():
    with pytest.raises(ObjectDoesNotExist):
        get_resource_for_path("https://example.com/")
