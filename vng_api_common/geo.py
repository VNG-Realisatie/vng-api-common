from rest_framework.exceptions import NotAcceptable
from rest_framework.renderers import BrowsableAPIRenderer

from .exceptions import PreconditionFailed

HEADER_ACCEPT = "Accept-Crs"
HEADER_CONTENT = "Content-Crs"

DEFAULT_CRS = "EPSG:4326"


def extract_header(request, name: str) -> str:
    _header = name.replace("-", "_").upper()
    header = f"HTTP_{_header}"
    return request.META.get(header)


class GeoMixin:
    """
    GeoJSON viewset mixin.
    """

    @property
    def default_response_headers(self):
        headers = super().default_response_headers
        headers["Content-Crs"] = DEFAULT_CRS
        return headers

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.perform_crs_negotation(request)

    def perform_crs_negotation(self, request):
        # don't cripple the browsable API...
        if isinstance(request.accepted_renderer, BrowsableAPIRenderer):
            return

        # methods with request bodies need to have the CRS specified
        if request.method.lower() in ("post", "put", "patch"):
            content_crs = extract_header(request, HEADER_CONTENT)
            if content_crs is None:
                raise PreconditionFailed(detail=f"'{HEADER_CONTENT}' header ontbreekt")
            if content_crs != DEFAULT_CRS:
                raise NotAcceptable(detail=f"CRS '{content_crs}' is niet ondersteund")

        if request.method.lower() == "delete":
            return

        # client must indicate which CRS they want in the response
        requested_crs = extract_header(request, HEADER_ACCEPT)
        if requested_crs is None:
            raise PreconditionFailed(detail=f"'{HEADER_ACCEPT}' header ontbreekt")

        if requested_crs != DEFAULT_CRS:
            raise NotAcceptable(detail=f"CRS '{requested_crs}' is niet ondersteund")
