import os
from urllib.parse import urlparse

from django.conf import settings

import yaml

DEFAULT_PATH_PARAMETERS = {
    'version': '1',
}

SPEC_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')

with open(SPEC_PATH, 'r') as infile:
    SPEC = yaml.load(infile)


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
