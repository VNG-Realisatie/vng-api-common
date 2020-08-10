from django.core.exceptions import ValidationError

import pytest

from testapp.models import Person
from vng_api_common.constants import FILTER_URL_DID_NOT_RESOLVE
from vng_api_common.filters import URLModelChoiceField
from vng_api_common.utils import NotAViewSet


def test_filter_field_url_to_pk_trailing_slash():
    field = URLModelChoiceField(queryset=Person.objects.all())
    with pytest.raises(NotAViewSet):
        field.url_to_pk("https://google.com/")


def test_filter_field_to_python_trailing_slash():
    field = URLModelChoiceField(queryset=Person.objects.all())
    value = field.to_python("https://google.com/")
    assert value == FILTER_URL_DID_NOT_RESOLVE


def test_filter_field_to_python_invalid_url_raises_error():
    field = URLModelChoiceField(queryset=Person.objects.all())
    with pytest.raises(ValidationError) as exc:
        field.to_python("thisisnotaurl")

    assert exc.value.code == "invalid"
