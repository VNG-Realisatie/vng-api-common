import time

import jwt
from rest_framework import status

from ..authorizations.models import (
    Applicatie, AuthorizationsConfig, Autorisatie
)
from ..constants import VertrouwelijkheidsAanduiding
from ..models import JWTSecret


def generate_jwt(scopes: list, secret: str='letmein', zaaktypes: list=None) -> str:
    scope_labels = sum((_get_scope_labels(scope) for scope in scopes), [])
    payload = {
        # standard claims
        'iss': 'testsuite',
        'iat': int(time.time()),
        # custom claims
        'zds': {
            'scopes': scope_labels,
            'zaaktypes': zaaktypes or [],
        },
    }
    headers = {
        'client_identifier': 'testsuite',
    }
    encoded = jwt.encode(payload, secret, headers=headers, algorithm='HS256')
    encoded = encoded.decode('ascii')
    return f"Bearer {encoded}"


def _get_scope_labels(scope) -> list:
    if not scope.children:
        return [scope.label]

    labels = []
    for child in scope.children:
        labels += _get_scope_labels(child)
    return sorted(set(labels))


class AuthCheckMixin:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        JWTSecret.objects.get_or_create(
            identifier='testsuite',
            defaults={'secret': 'letmein'}
        )

    def assertForbidden(self, url, method='get', request_kwargs=None):
        """
        Assert that an appropriate scope is required.
        """
        do_request = getattr(self.client, method)
        request_kwargs = request_kwargs or {}

        with self.subTest(case='JWT missing'):
            response = do_request(url, **request_kwargs)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        with self.subTest(case='Invalid JWT structure'):
            invalid_jwt = generate_jwt_auth('testsuite', 'letmein')[:-10]
            self.client.credentials(HTTP_AUTHORIZATION=invalid_jwt)

            response = do_request(url, **request_kwargs)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def assertForbiddenWithCorrectScope(
            self, url: str, scopes: list, method='get',
            request_kwargs=None, **extra_claims):

        do_request = getattr(self.client, method)
        request_kwargs = request_kwargs or {}

        jwt = generate_jwt(scopes=scopes, **extra_claims)
        self.client.credentials(HTTP_AUTHORIZATION=jwt)

        response = do_request(url, **request_kwargs)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class JWTScopesMixin:

    scopes = None
    zaaktypes = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        JWTSecret.objects.get_or_create(
            identifier='testsuite',
            defaults={'secret': 'letmein'}
        )

    def setUp(self):
        super().setUp()

        if self.scopes is not None:
            token = generate_jwt(
                scopes=self.scopes,
                zaaktypes=self.zaaktypes or [],
                secret='letmein'
            )
            self.client.credentials(HTTP_AUTHORIZATION=token)


# tools fot testing with new authorization format
def generate_jwt_auth(client_id, secret):
    payload = {
        # standard claims
        'iss': 'testsuite',
        'iat': int(time.time()),
        # custom
        'client_id': client_id
    }
    encoded = jwt.encode(payload, secret, algorithm='HS256')
    encoded = encoded.decode('ascii')
    return f"Bearer {encoded}"


class JWTAuthMixin:
    scopes = None
    heeft_alle_autorisaties = False
    zaaktype = None
    informatieobjecttype = None
    besluittype = None
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduiding.zeer_geheim

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        JWTSecret.objects.get_or_create(
            identifier='testsuite',
            defaults={'secret': 'letmein'}
        )

        config = AuthorizationsConfig.get_solo()

        cls.applicatie = Applicatie.objects.create(
            client_ids=['testsuite'],
            label='for test',
            heeft_alle_autorisaties=cls.heeft_alle_autorisaties
        )

        if cls.heeft_alle_autorisaties is False:
            cls.autorisatie = Autorisatie.objects.create(
                applicatie=cls.applicatie,
                component=config.component,
                scopes=cls.scopes or [],
                zaaktype=cls.zaaktype or '',
                informatieobjecttype=cls.informatieobjecttype or '',
                besluittype=cls.besluittype or '',
                max_vertrouwelijkheidaanduiding=cls.max_vertrouwelijkheidaanduiding
            )

    def setUp(self):
        super().setUp()

        token = generate_jwt_auth(client_id='testsuite', secret='letmein')
        self.client.credentials(HTTP_AUTHORIZATION=token)
