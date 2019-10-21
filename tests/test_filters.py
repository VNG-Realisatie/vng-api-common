import pytest
from django.core.exceptions import ObjectDoesNotExist

from testapp.models import Person
from vng_api_common.filters import URLModelChoiceField

def test_filter_field_url_to_pk_trailing_slash():
    field = URLModelChoiceField(queryset=Person.objects.all())
    with pytest.raises(ObjectDoesNotExist):
        field.url_to_pk("https://google.com/")
