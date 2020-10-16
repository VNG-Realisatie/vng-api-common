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
        parser.add_argument(
            "api-spec", help="Path to the openapi spec. Will be overwritten!"
        )

    def handle(self, **options):
        source = options["api-spec"]

        # Enforce the file to be read as UTF-8 to prevent any platform
        # dependent encoding.
        with open(source, "r", encoding="utf8") as infile:
            spec = yaml.safe_load(infile)

            for status, response in spec["components"]["responses"].items():
                if not (400 <= int(status) < 600):
                    continue

                content = {}
                for contenttype, _response in response["content"].items():
                    if contenttype == "application/json":
                        contenttype = ERROR_CONTENT_TYPE
                    content[contenttype] = _response

                response["content"] = content

        with open(source, "w", encoding="utf8") as outfile:
            yaml.dump(spec, outfile, default_flow_style=False)
