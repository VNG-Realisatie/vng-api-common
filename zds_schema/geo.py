from rest_framework.exceptions import NotAcceptable
from rest_framework.renderers import BrowsableAPIRenderer

from .exceptions import PreconditionFailed

HEADER_ACCEPT = 'Accept-Crs'
HEADER_CONTENT = 'Content-Crs'

DEFAULT_CRS = 'EPSG:4326'


class GeoMixin:
    """
    GeoJSON viewset mixin.
    """
    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers['Content-Crs'] = DEFAULT_CRS
        return headers

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.perform_crs_negotation(request)

    def perform_crs_negotation(self, request):
        # don't cripple the browsable API...
        if isinstance(request.accepted_renderer, BrowsableAPIRenderer):
            return

        _header = HEADER_ACCEPT.replace('-', '_').upper()
        header = f'HTTP_{_header}'
        requested_crs = request.META.get(header)
        if requested_crs is None:
            raise PreconditionFailed(
                detail=F"'{HEADER_ACCEPT}' header ontbreekt",
            )

        if requested_crs != DEFAULT_CRS:
            raise NotAcceptable(
                detail=f"CRS '{requested_crs}' is niet ondersteund",
            )
