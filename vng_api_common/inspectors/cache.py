from collections import OrderedDict

from django.utils.translation import gettext_lazy as _

from drf_yasg import openapi
from rest_framework.views import APIView

from ..caching.introspection import has_cache_header

CACHE_REQUEST_HEADERS = [
    openapi.Parameter(
        name="If-None-Match",
        type=openapi.TYPE_STRING,
        in_=openapi.IN_HEADER,
        required=False,
        description=_(
            "Perform conditional requests. This header should contain one or "
            "multiple ETag values of resources the client has cached. If the "
            "current resource ETag value is in this set, then an HTTP 304 "
            "empty body will be returned. See "
            "[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match) "
            "for details."
        ),
        examples={
            "oneValue": {
                "summary": _("One ETag value"),
                "value": '"79054025255fb1a26e4bc422aef54eb4"',
            },
            "multipleValues": {
                "summary": _("Multiple ETag values"),
                "value": '"79054025255fb1a26e4bc422aef54eb4", "e4d909c290d0fb1ca068ffaddf22cbd0"',
            },
        },
    )
]


def get_cache_headers(view: APIView) -> OrderedDict:
    if not has_cache_header(view):
        return OrderedDict()

    return OrderedDict(
        (
            (
                "ETag",
                openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_(
                        "De ETag berekend op de response body JSON. "
                        "Indien twee resources exact dezelfde ETag hebben, dan zijn "
                        "deze resources identiek aan elkaar. Je kan de ETag gebruiken "
                        "om caching te implementeren."
                    ),
                ),
            ),
        )
    )
