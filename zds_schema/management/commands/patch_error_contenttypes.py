"""
Patch the content-type of error responses.

Due to the changes between Swagger 2.0 and OpenAPI 3.0, we cannot handle
this at the Python level.
"""
from django.core.management import BaseCommand

import oyaml as yaml

from ...views import ERROR_CONTENT_TYPE


class Command(BaseCommand):
    help = "Patch the error-response content types in the OAS 3 spec"

    def add_arguments(self, parser):
        parser.add_argument('api-spec', help="Path to the openapi spec. Will be overwritten!")

    def handle(self, **options):
        source = options['api-spec']
        with open(source, 'r') as infile:
            spec = yaml.safe_load(infile)

        for path, methods in spec['paths'].items():
            for method in methods.values():
                if 'responses' not in method:
                    continue

                for status, response in method['responses'].items():
                    if not (400 <= int(status) < 600):
                        continue

                    content = {}
                    for contenttype, _response in response['content'].items():
                        if contenttype == 'application/json':
                            contenttype = ERROR_CONTENT_TYPE
                        content[contenttype] = _response

                    response['content'] = content

        with open(source, 'w') as outfile:
            yaml.dump(spec, outfile, default_flow_style=False)
