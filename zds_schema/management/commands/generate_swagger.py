import logging
import os

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.management.commands import generate_swagger
from rest_framework.settings import api_settings

from ...schema import OpenAPISchemaGenerator


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

    # need to overwrite the generator class...
    def handle(self, output_file, overwrite, format, api_url, mock, user, private, *args, **options):
        # disable logs of WARNING and below
        logging.disable(logging.WARNING)

        info = getattr(swagger_settings, 'DEFAULT_INFO', None)
        if not isinstance(info, openapi.Info):
            raise ImproperlyConfigured(
                'settings.SWAGGER_SETTINGS["DEFAULT_INFO"] should be an '
                'import string pointing to an openapi.Info object'
            )

        if not format:
            if os.path.splitext(output_file)[1] in ('.yml', '.yaml'):
                format = 'yaml'
        format = format or 'json'

        api_url = api_url or swagger_settings.DEFAULT_API_URL

        user = User.objects.get(username=user) if user else None
        mock = mock or private or (user is not None)
        if mock and not api_url:
            raise ImproperlyConfigured(
                '--mock-request requires an API url; either provide '
                'the --url argument or set the DEFAULT_API_URL setting'
            )

        request = self.get_mock_request(api_url, format, user) if mock else None

        generator = OpenAPISchemaGenerator(
            info=info,
            url=api_url
        )
        schema = generator.get_schema(request=request, public=not private)

        if output_file == '-':
            self.write_schema(schema, self.stdout, format)
        else:
            # normally this would be easily done with open(mode='x'/'w'),
            # but python 2 is a pain in the ass as usual
            flags = os.O_CREAT | os.O_WRONLY
            flags = flags | (os.O_TRUNC if overwrite else os.O_EXCL)
            with os.fdopen(os.open(output_file, flags), "w") as stream:
                self.write_schema(schema, stream, format)
