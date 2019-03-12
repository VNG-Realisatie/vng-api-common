import time

import jwt
from rest_framework import status

from ..models import JWTSecret
from ..scopes import Scope


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

    def assertForbidden(self, url, method='get'):
        """
        Assert that an appropriate scope is required.
        """
        do_request = getattr(self.client, method)

        with self.subTest(case='JWT missing'):
            response = do_request(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(case='Invalid JWT structure'):
            invalid_jwt = generate_jwt(scopes=[Scope('invalid.scope')])[:-10]
            self.client.credentials(HTTP_AUTHORIZATION=invalid_jwt)

            response = do_request(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(case='Correct scope missing'):
            jwt = generate_jwt(scopes=[Scope('invalid.scope')])
            self.client.credentials(HTTP_AUTHORIZATION=jwt)

            response = do_request(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
