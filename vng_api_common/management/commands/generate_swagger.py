import logging
import os

from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.module_loading import import_string

from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.management.commands import generate_swagger
from rest_framework.settings import api_settings

from ...schema import OpenAPISchemaGenerator
from ...version import get_major_version


class Table:
    def __init__(self, resource: str):
        self.resource = resource
        self.rows = []


class Row:
    def __init__(
        self,
        label: str,
        description: str,
        type: str,
        required: bool,
        create: bool,
        read: bool,
        update: bool,
        delete: bool,
    ):
        self.label = label
        self.description = description
        self.type = type
        self.required = required
        self.create = create
        self.read = read
        self.update = update
        self.delete = delete


class Command(generate_swagger.Command):
    """
    Patches to the provided command to modify the schema for ZDS needs.
    """

    leave_locale_alone = True

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--to-markdown-table", action="store_true")

        parser.add_argument(
            "--info", dest="info", default=None, help="Path to schema info object"
        )

        parser.add_argument(
            "--urlconf",
            dest="urlconf",
            default=None,
            help="Urlconf for schema generator",
        )

    def get_mock_request(self, *args, **kwargs):
        request = super().get_mock_request(*args, **kwargs)
        request.version = api_settings.DEFAULT_VERSION
        return request

    def write_schema(self, schema, stream, format):
        del schema.host
        del schema.schemes
        super().write_schema(schema, stream, format)

    # need to overwrite the generator class...
    def handle(
        self,
        output_file,
        overwrite,
        format,
        api_url,
        mock,
        user,
        private,
        info=None,
        urlconf=None,
        *args,
        **options,
    ):
        # disable logs of WARNING and below
        logging.disable(logging.WARNING)

        if info:
            info = import_string(info)
        else:
            info = getattr(swagger_settings, "DEFAULT_INFO", None)
        if not isinstance(info, openapi.Info):
            raise ImproperlyConfigured(
                'settings.SWAGGER_SETTINGS["DEFAULT_INFO"] should be an '
                "import string pointing to an openapi.Info object"
            )

        if not format:
            if os.path.splitext(output_file)[1] in (".yml", ".yaml"):
                format = "yaml"
        format = format or "json"

        api_root = reverse("api-root", kwargs={"version": get_major_version()})
        api_url = (
            api_url
            or swagger_settings.DEFAULT_API_URL  # noqa
            or f"http://example.com{api_root}"  # noqa
        )

        user = User.objects.get(username=user) if user else None
        mock = mock or private or (user is not None)
        if mock and not api_url:
            raise ImproperlyConfigured(
                "--mock-request requires an API url; either provide "
                "the --url argument or set the DEFAULT_API_URL setting"
            )

        request = self.get_mock_request(api_url, format, user) if mock else None

        generator = OpenAPISchemaGenerator(info=info, url=api_url, urlconf=urlconf)
        schema = generator.get_schema(request=request, public=not private)

        if output_file == "-":
            self.write_schema(schema, self.stdout, format)
        else:
            with open(output_file, "w", encoding="utf8") as stream:
                if options["to_markdown_table"]:
                    self.to_markdown_table(schema, stream)
                else:
                    self.write_schema(schema, stream, format)

    def to_markdown_table(self, schema, stream):
        template = "vng_api_common/api_schema_to_markdown_table.md"
        tables = []

        whitelist = [model._meta.object_name for model in apps.get_models()]

        for resource, definition in schema.definitions.items():
            if resource not in whitelist:
                continue

            if not hasattr(definition, "properties"):
                continue

            table = Table(resource)
            for field, _schema in definition.properties.items():
                if isinstance(_schema, openapi.SchemaRef):
                    continue
                required = (
                    hasattr(definition, "required") and field in definition.required
                )

                readonly = getattr(_schema, "readOnly", False)
                table.rows.append(
                    Row(
                        label=field,
                        description=getattr(_schema, "description", ""),
                        type=_schema.type,
                        required=required,
                        create=not readonly,
                        read=True,
                        update=not readonly,
                        delete=not readonly,
                    )
                )
            tables.append(table)

        markdown = render_to_string(template, context={"tables": tables})
        stream.write(markdown)
