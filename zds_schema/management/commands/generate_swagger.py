from drf_yasg.management.commands import generate_swagger
from rest_framework.settings import api_settings


class Command(generate_swagger.Command):
    """
    Patches to the provided command to modify the schema for ZDS needs.
    """

    def get_mock_request(self, *args, **kwargs):
        request = super().get_mock_request(*args, **kwargs)
        request.version = api_settings.DEFAULT_VERSION
        return request

    def write_schema(self, schema, stream, format):
        del schema.host
        del schema.schemes
        super().write_schema(schema, stream, format)
