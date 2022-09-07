import logging
import json
import yaml

from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from drf_spectacular.plumbing import get_relative_url
from drf_spectacular.renderers import (
    OpenApiJsonRenderer,
    OpenApiJsonRenderer2,
    OpenApiYamlRenderer,
    OpenApiYamlRenderer2,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularJSONAPIView, SpectacularRedocView, SpectacularYAMLAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


class SchemaViewRedoc(SpectacularRedocView):
    def _get_schema_url(self, request) -> str:
        schema_url = self.url or get_relative_url(
            reverse(self.url_name, request=request)
        )
        return f"{schema_url}openapi.yaml"


class SchemaViewAPI(SpectacularYAMLAPIView):
    def _get_schema_response(self, request):
        filename = "openapi.yaml"

        with open(Path(settings.BASE_DIR) / "src" / filename, "r") as file:
            schema = yaml.safe_load(file)

        return Response(
            data=schema,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
