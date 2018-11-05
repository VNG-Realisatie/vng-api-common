# https://pyjwt.readthedocs.io/en/latest/usage.html#reading-headers-without-validation
# -> we can put the organization/service in the headers itself
from django.conf import settings
from django.utils.functional import cached_property

import jwt

EMPTY_PAYLOAD = {
    'scopes': [],
}


class JWTPayload:

    def __init__(self, encoded_payload: str=None):
        self.encoded_payload = encoded_payload

    @cached_property
    def payload(self) -> dict:
        if self.encoded_payload is None:
            return EMPTY_PAYLOAD

        # TODO - make dynamic
        key = settings.JWT_SECRET

        # the jwt package does verification against tampering (TODO: unit test)
        payload = jwt.decode(self.encoded_payload, key, algorithms='HS256')

        return payload

    def has_scopes(self, scopes: list) -> bool:
        """
        Check whether all of the expected scopes are present or not.
        """
        scopes_provided = self.payload['scopes']
        # simple form - needs a more complex setup if a scope 'bundles'
        # other scopes
        return set(scopes).issubset(set(scopes_provided))


class AuthMiddleware:

    header = 'HTTP_AUTHORIZATION'

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.extract_jwt_payload(request)
        return self.get_response(request) if self.get_response else None

    def extract_jwt_payload(self, request):
        encoded = request.META.get(self.header)
        request.jwt_payload = JWTPayload(encoded)
