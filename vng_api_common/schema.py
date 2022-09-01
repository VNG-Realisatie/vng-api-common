import logging

from drf_spectacular.plumbing import get_relative_url
from drf_spectacular.renderers import (
    OpenApiJsonRenderer,
    OpenApiJsonRenderer2,
    OpenApiYamlRenderer,
    OpenApiYamlRenderer2,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


class SchemaViewRedoc(SpectacularRedocView):
    def _get_schema_url(self, request) -> str:
        schema_url = self.url or get_relative_url(
            reverse(self.url_name, request=request)
        )
        return f"{schema_url}openapi.yaml"


class SchemaViewAPI(SpectacularAPIView):
    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        if ".yaml" in self.request.path:
            self.renderer_classes = [OpenApiYamlRenderer, OpenApiYamlRenderer2]
        elif ".json" in self.request.path:
            self.renderer_classes = [OpenApiJsonRenderer, OpenApiJsonRenderer2]

        return [renderer() for renderer in self.renderer_classes]
