from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _

from drf_yasg import openapi
from rest_framework.views import APIView

from ..caching.introspection import has_cache_header


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
