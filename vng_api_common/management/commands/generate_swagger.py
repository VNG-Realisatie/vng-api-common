import logging
import os

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string

from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.management.commands.spectacular import (
    Command as SpectacularCommand,
)
from drf_spectacular.settings import spectacular_settings
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

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


class Command(SpectacularCommand):
    """
    Patches to the provided command to modify the schema for ZDS needs.
    """

    leave_locale_alone = True

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--output-file", dest="output_file", default=None, type=str)
        parser.add_argument("--to-markdown-table", action="store_true")
        parser.add_argument(
            "-o",
            "--overwrite",
            default=False,
            action="store_true",
            help="Overwrite the output file if it already exists. "
            "Default behavior is to stop if the output file exists.",
        )
        parser.add_argument(
            "-m",
            "--mock-request",
            dest="mock",
            default=False,
            action="store_true",
            help="Use a mock request when generating the swagger schema. This is useful if your views or serializers "
            "depend on context from a request in order to function.",
        )
        parser.add_argument(
            "-u",
            "--url",
            dest="api_url",
            default="",
            type=str,
            help="Base API URL - sets the host and scheme attributes of the generated document.",
        )
        parser.add_argument(
            "--user",
            dest="user",
            help="Username of an existing user to use for mocked authentication. This option implies --mock-request.",
        )
        parser.add_argument(
            "-p",
            "--private",
            default=False,
            action="store_true",
            help="Hides endpoints not accesible to the target user. If --user is not given, only shows endpoints that "
            "are accesible to unauthenticated users.\n"
            "This has the same effect as passing public=False to get_schema_view() or "
            "OpenAPISchemaGenerator.get_schema().\n"
            "This option implies --mock-request.",
        )

    def get_mock_request(self, url, format, user=None):
        factory = APIRequestFactory()

        request = factory.get(url + format)
        if user is not None:
            force_authenticate(request, user=user)
        request = APIView().initialize_request(request)
        request.version = api_settings.DEFAULT_VERSION
        return request

    # need to overwrite the generator class...
    def handle(
        self,
        output_file,
        overwrite,
        format,
        api_url,
        mock,
        api_version,
        user,
        private,
        generator_class,
        urlconf=None,
        **options,
    ):
        # disable logs of WARNING and below
        logging.disable(logging.WARNING)
        if not format:
            if os.path.splitext(output_file)[1] in (".yml", ".yaml"):
                format = "openapi"
        format = format or "openapi-json"

        try:
            api_root = reverse("api-root", kwargs={"version": get_major_version()})
        except NoReverseMatch:
            api_root = reverse("api-root")
        api_url = api_url or f"http://example.com{api_root}"  # noqa
        if user:
            # Only call get_user_model if --user was passed in order to
            # avoid crashing if auth is not configured in the project
            user = get_user_model().objects.get(username=user)

        mock = mock or private or (user is not None) or (api_version is not None)
        if mock and not api_url:
            raise ImproperlyConfigured(
                "--mock-request requires an API url; either provide "
                "the --url argument or set the DEFAULT_API_URL setting"
            )

        request = None
        if mock:
            request = self.get_mock_request(api_url, format, user)

        api_version = api_version or api_settings.DEFAULT_VERSION
        if request and api_version:
            request.version = api_version

        if generator_class:
            generator_class_import = import_string(generator_class)
        else:
            generator_class_import = spectacular_settings.DEFAULT_GENERATOR_CLASS

        generator = generator_class_import(
            urlconf=urlconf, api_version=api_version, url=api_url
        )

        schema = generator.get_schema(request=request, public=not private)

        GENERATOR_STATS.emit_summary()

        if output_file == "-":
            self.write_schema(schema, self.stdout, format)
        else:
            with open(output_file, "w", encoding="utf8") as stream:
                if options["to_markdown_table"]:
                    self.to_markdown_table(schema, stream)
                else:
                    renderer = self.get_renderer(format)
                    output = renderer.render(schema, renderer_context={})

                    if output_file:
                        with open(output_file, "wb") as f:
                            f.write(output)
                    else:
                        self.stdout.write(output.decode())

    def to_markdown_table(self, schema, stream):
        template = "vng_api_common/api_schema_to_markdown_table.md"
        tables = []

        whitelist = [model._meta.object_name for model in apps.get_models()]
        for resource, definition in schema["components"]["schemas"].items():
            if resource not in whitelist:
                continue
            properties = definition.get("properties", False)
            if not properties:
                continue

            table = Table(resource)
            for field, _schema in properties.items():
                if field == "$ref":
                    continue

                required = field in definition.get("required", {})

                readonly = _schema.get("readOnly", False)

                table.rows.append(
                    Row(
                        label=field,
                        description=_schema.get("description", ""),
                        type=_schema.get("type", ""),
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
