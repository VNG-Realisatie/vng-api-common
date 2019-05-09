import os
from urllib.parse import urlparse

from django.conf import settings

import yaml

DEFAULT_PATH_PARAMETERS = {
    'version': '1',
}

SPEC_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')

with open(SPEC_PATH, 'r') as infile:
    SPEC = yaml.safe_load(infile)


def get_operation_url(operation, **kwargs):
    url = SPEC['servers'][0]['url']
    base_path = urlparse(url).path

    for path, methods in SPEC['paths'].items():
        for name, method in methods.items():
            if name == 'parameters':
                continue

            if method['operationId'] == operation:
                format_kwargs = DEFAULT_PATH_PARAMETERS.copy()
                format_kwargs.update(**kwargs)
                path = path.format(**format_kwargs)
                return f"{base_path}{path}"

    raise ValueError(f"Operation {operation} not found")


class TypeCheckMixin:

    def assertResponseTypes(self, response_data: dict, types: tuple):
        """
        Do type checks on the response data.

        :param types: tuple of (field_name, class)
        :raises AssertionError: if the type mismatches
        """
        for field, type_ in types:
            with self.subTest(field=field, type=type_):
                self.assertIsInstance(response_data[field], type_)


def get_validation_errors(response, field, index=0):
    """
    Assumes there's only one validation error for the field.
    """
    assert response.status_code == 400
    i = 0
    for error in response.data['invalid_params']:
        if error['name'] != field:
            continue

        if i == index:
            return error

        i += 1
