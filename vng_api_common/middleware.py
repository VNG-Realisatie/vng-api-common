# https://pyjwt.readthedocs.io/en/latest/usage.html#reading-headers-without-validation
# -> we can put the organization/service in the headers itself
import logging

from django.conf import settings

from rest_framework.response import Response

from .constants import VERSION_HEADER

logger = logging.getLogger(__name__)


class APIVersionHeaderMiddleware:
    """
    Include a header specifying the API-version
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if self.get_response is None:
            return None

        response = self.get_response(request)

        # not an API response, exit early
        if not isinstance(response, Response):
            return response

        # set the header
        response[VERSION_HEADER] = settings.API_VERSION

        return response
