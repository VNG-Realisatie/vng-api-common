import json
import logging
import os
from urllib.parse import urlsplit

from django.conf import settings
from django.urls import get_script_prefix

from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.codecs import yaml_sane_dump, yaml_sane_load
from drf_yasg.generators import OpenAPISchemaGenerator as _OpenAPISchemaGenerator
from drf_yasg.renderers import SwaggerJSONRenderer, SwaggerYAMLRenderer, _SpecRenderer
from drf_yasg.utils import get_consumes, get_produces
from drf_yasg.views import get_schema_view
from rest_framework import exceptions, permissions
from rest_framework.response import Response
from rest_framework.settings import api_settings

logger = logging.getLogger(__name__)


class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        """
        Rewrite parent class to add 'responses' in components
        """
        endpoints = self.get_endpoints(request)
        components = self.reference_resolver_class(
            openapi.SCHEMA_DEFINITIONS, "responses", force_init=True
        )
        self.consumes = get_consumes(api_settings.DEFAULT_PARSER_CLASSES)
        self.produces = get_produces(api_settings.DEFAULT_RENDERER_CLASSES)
        paths, prefix = self.get_paths(endpoints, components, request, public)

        security_definitions = self.get_security_definitions()
        if security_definitions:
            security_requirements = self.get_security_requirements(security_definitions)
        else:
            security_requirements = None

        url = self.url
        if url is None and request is not None:
            url = request.build_absolute_uri()

        return openapi.Swagger(
            info=self.info,
            paths=paths,
            consumes=self.consumes or None,
            produces=self.produces or None,
            security_definitions=security_definitions,
            security=security_requirements,
            _url=url,
            _prefix=prefix,
            _version=self.version,
            **dict(components),
        )

    def get_path_parameters(self, path, view_cls):
        """Return a list of Parameter instances corresponding to any templated path variables.

        :param str path: templated request path
        :param type view_cls: the view class associated with the path
        :return: path parameters
        :rtype: list[openapi.Parameter]
        """
        parameters = super().get_path_parameters(path, view_cls)

        # see if we can specify UUID a bit more
        for parameter in parameters:
            # the most pragmatic of checks
            if not parameter.name.endswith("_uuid"):
                continue
            parameter.format = openapi.FORMAT_UUID
            parameter.description = "Unieke resource identifier (UUID4)"
        return parameters


DefaultSchemaView = get_schema_view(
    # validators=['flex', 'ssv'],
    generator_class=OpenAPISchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class OpenAPIV3RendererMixin:
    def render(self, data, media_type=None, renderer_context=None):
        if "openapi" in data or "swagger" in data:
            if self.format == ".yaml":
                return yaml_sane_dump(data, False)
            elif self.format == ".json":
                return json.dumps(data)

        return super().render(
            data, media_type=media_type, renderer_context=renderer_context
        )


SPEC_RENDERERS = (
    type("SwaggerYAMLRenderer", (OpenAPIV3RendererMixin, SwaggerYAMLRenderer), {}),
    type("SwaggerJSONRenderer", (OpenAPIV3RendererMixin, SwaggerJSONRenderer), {}),
)


class SchemaView(DefaultSchemaView):
    """
    Always serve the v3 version, which is kept in version control.

    .. warn:: there is a risk of the generated schema not being in sync with
      the code. Unfortunately, that's the tradeoff we have. We could set up
      CI to check for outdated schemas.
    """

    schema_path = None

    @property
    def _is_openapi_v2(self) -> bool:
        default = "3" if "format" in self.kwargs else "2"
        version = self.request.GET.get("v", default)
        return version.startswith("2")

    def get_renderers(self):
        if self._is_openapi_v2:
            return super().get_renderers()
        return [renderer() for renderer in SPEC_RENDERERS]

    def get_schema_path(self) -> str:
        return self.schema_path or os.path.join(
            settings.BASE_DIR, "src", "openapi.yaml"
        )

    def get(self, request, version="", *args, **kwargs):
        if self._is_openapi_v2:
            version = request.version or version or ""
            if isinstance(request.accepted_renderer, _SpecRenderer):
                generator = self.generator_class(
                    getattr(self, "info", swagger_settings.DEFAULT_INFO),
                    version,
                    None,
                    None,
                    None,
                )
            else:
                generator = self.generator_class(
                    getattr(self, "info", swagger_settings.DEFAULT_INFO),
                    version,
                    None,
                    patterns=[],
                )

            schema = generator.get_schema(request, self.public)
            if schema is None:
                raise exceptions.PermissionDenied()  # pragma: no cover
            return Response(schema)

        # serve the staticically included V3 schema
        SCHEMA_PATH = self.get_schema_path()
        with open(SCHEMA_PATH, "r") as infile:
            schema = yaml_sane_load(infile)

        # fix the servers
        for server in schema["servers"]:
            split_url = urlsplit(server["url"])
            if split_url.netloc:
                continue

            prefix = get_script_prefix()
            if prefix.endswith("/"):
                prefix = prefix[:-1]
            server_path = f"{prefix}{server['url']}"
            server["url"] = request.build_absolute_uri(server_path)

        return Response(data=schema, headers={"X-OAS-Version": schema["openapi"]})
