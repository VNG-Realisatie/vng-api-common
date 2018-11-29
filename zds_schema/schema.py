import json
import logging
import os
from urllib.parse import urlsplit

from django.conf import settings

from drf_yasg import openapi
from drf_yasg.codecs import yaml_sane_dump, yaml_sane_load
from drf_yasg.generators import (
    OpenAPISchemaGenerator as _OpenAPISchemaGenerator
)
from drf_yasg.renderers import SwaggerJSONRenderer, SwaggerYAMLRenderer
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):

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
            if not parameter.name.endswith('_uuid'):
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
        if 'openapi' in data or 'swagger' in data:
            if self.format == '.yaml':
                return yaml_sane_dump(data, False)
            elif self.format == '.json':
                return json.dumps(data)

        return super().render(data, media_type=media_type, renderer_context=renderer_context)


SPEC_RENDERERS = (
    type(
        'SwaggerYAMLRenderer',
        (OpenAPIV3RendererMixin, SwaggerYAMLRenderer),
        {},
    ),
    type(
        'SwaggerJSONRenderer',
        (OpenAPIV3RendererMixin, SwaggerJSONRenderer),
        {},
    ),
)


class SchemaView(DefaultSchemaView):

    @property
    def _is_openapi_v3(self) -> bool:
        version = self.request.GET.get('v', '')
        return version.startswith('3')

    def get_renderers(self):
        if not self._is_openapi_v3:
            return super().get_renderers()
        return [renderer() for renderer in SPEC_RENDERERS]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        if not self._is_openapi_v3:
            return response

        # serve the staticically included V3 schema
        SCHEMA_PATH = os.path.join(settings.BASE_DIR, 'src', 'openapi.yaml')
        with open(SCHEMA_PATH, 'r') as infile:
            schema = yaml_sane_load(infile)

        # fix the servers
        for server in schema['servers']:
            split_url = urlsplit(server['url'])
            if split_url.netloc:
                continue

            prefix = settings.FORCE_SCRIPT_NAME or ''
            if prefix.endswith('/'):
                prefix = prefix[:-1]
            server_path = f"{prefix}{server['url']}"
            server['url'] = request.build_absolute_uri(server_path)

        return Response(
            data=schema,
            headers={'X-OAS-Version': schema['openapi']}
        )
