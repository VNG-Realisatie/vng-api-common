# https://pyjwt.readthedocs.io/en/latest/usage.html#reading-headers-without-validation
# -> we can put the organization/service in the headers itself
import logging
from typing import Union

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

import jwt
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .constants import VERSION_HEADER
from .models import JWTSecret
from .scopes import Scope

logger = logging.getLogger(__name__)

EMPTY_PAYLOAD = {
    'scopes': [],
    'zaaktypes': [],
}


class JWTPayload:

    def __init__(self, encoded: str=None):
        self.encoded = encoded

    def __repr__(self):
        return "<%s: payload=%r>" % (self.__class__.__name__, self.payload)

    def __getitem__(self, key):
        return self.payload[key]

    def get(self, attr, *args, **kwargs):
        return self.payload.get(attr, *args, **kwargs)

    @cached_property
    def payload(self) -> dict:
        if self.encoded is None:
            return EMPTY_PAYLOAD

        try:
            header = jwt.get_unverified_header(self.encoded)
        except jwt.DecodeError:
            logger.info("Invalid JWT encountered")
            raise PermissionDenied(
                _('JWT could not be decoded. Possibly you made a copy-paste mistake.'),
                code='jwt-decode-error'
            )

        try:
            jwt_secret = JWTSecret.objects.get(identifier=header['client_identifier'])
        except JWTSecret.DoesNotExist:
            raise PermissionDenied(
                'Client identifier bestaat niet',
                code='invalid-client-identifier'
            )
        except KeyError:
            raise PermissionDenied(
                'Client identifier is niet aanwezig in JWT',
                code='missing-client-identifier'
            )
        else:
            key = jwt_secret.secret

        # the jwt package does verification against tampering (TODO: unit test)
        try:
            payload = jwt.decode(self.encoded, key, algorithms='HS256')
        except jwt.InvalidSignatureError as exc:
            logger.exception("Invalid signature - possible payload tampering?")
            raise PermissionDenied(
                'Client credentials zijn niet geldig',
                code='invalid-jwt-signature'
            )

        return payload.get('zds', EMPTY_PAYLOAD)

    def has_scopes(self, scopes: Union[Scope, None]) -> bool:
        """
        Check whether all of the expected scopes are present or not.
        """
        if scopes is None:
            # TODO: should block instead of allow it - we'll gradually introduce this
            return True

        scopes_provided = self.payload['scopes']
        # simple form - needs a more complex setup if a scope 'bundles'
        # other scopes
        return scopes.is_contained_in(scopes_provided)


class AuthMiddleware:

    header = 'HTTP_AUTHORIZATION'
    auth_type = 'Bearer'

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.extract_jwt_payload(request)
        return self.get_response(request) if self.get_response else None

    def extract_jwt_payload(self, request):
        authorization = request.META.get(self.header, '')
        prefix = f"{self.auth_type} "
        if authorization.startswith(prefix):
            # grab the actual token
            encoded = authorization[len(prefix):]
        else:
            encoded = None

        request.jwt_payload = JWTPayload(encoded)


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
