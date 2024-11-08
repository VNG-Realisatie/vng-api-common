from unittest.mock import patch

import pytest
import requests_mock
from rest_framework.serializers import ValidationError

from vng_api_common.validators import PublishValidator


@patch("vng_api_common.validators.obj_has_shape", return_value=True)
@patch("vng_api_common.validators.fetcher")
def publish_validate(value, *mocks):
    api_spec = "http://example.com/src/openapi.yaml"
    validator = PublishValidator("Resource", api_spec, lambda x: {})

    url = "http://example.com/src/resource/1"
    with requests_mock.Mocker() as m:
        m.get(url, json=value)

        result = validator(url)

    return result


def test_publish_validator_concept_true():
    with pytest.raises(ValidationError) as err:
        publish_validate({"concept": True})

    error = err.value.detail

    assert error[0].code == "not-published"


def test_publish_validator_concept_false():
    publish_validate({"concept": False})


def test_publish_validator_concept_empty():
    publish_validate({})
