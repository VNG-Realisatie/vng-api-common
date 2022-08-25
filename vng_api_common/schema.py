import logging
from rest_framework.reverse import reverse

from drf_spectacular.plumbing import get_relative_url
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

logger = logging.getLogger(__name__)


class SchemaViewRedoc(SpectacularRedocView):
    def _get_schema_url(self, request) -> str:
        schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
        return f"{schema_url}openapi.yaml"


class SchemaViewAPI(SpectacularAPIView):
    pass
