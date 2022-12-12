import time
from typing import List, Optional

import jwt
from rest_framework import status

from ..authorizations.models import Applicatie, AuthorizationsConfig, Autorisatie
from ..constants import VertrouwelijkheidsAanduiding
from ..models import JWTSecret


class AuthCheckMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        JWTSecret.objects.get_or_create(
            identifier="testsuite", defaults={"secret": "letmein"}
        )

    def assertForbidden(self, url, method="get", request_kwargs=None):
        """
        Assert that an appropriate scope is required.
        """
        do_request = getattr(self.client, method)
        request_kwargs = request_kwargs or {}

        with self.subTest(case="JWT missing"):
            response = do_request(url, **request_kwargs)

            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN, response.data
            )

        with self.subTest(case="Invalid JWT structure"):
            invalid_jwt = generate_jwt_auth("testsuite", "letmein")[:-10]
            self.client.credentials(HTTP_AUTHORIZATION=invalid_jwt)

            response = do_request(url, **request_kwargs)

            self.assertEqual(
                response.status_code, status.HTTP_403_FORBIDDEN, response.data
            )


def generate_jwt_auth(
    client_id, secret, user_id="test_user_id", user_representation="Test User"
):
    """
    Generate a JWT suitable for the second version of the AC-based auth.
    """
    payload = {
        # standard claims
        "iss": "testsuite",
        "iat": int(time.time()),
        # custom
        "client_id": client_id,
        "user_id": user_id,
        "user_representation": user_representation,
    }
    encoded = jwt.encode(payload, secret, algorithm="HS256")
    return f"Bearer {encoded}"


class JWTAuthMixin:
    """
    Configure the local auth cache.

    Creates the local auth objects for permission checks, as if you're talking
    to a real AC behind the scenes.
    """

    client_id = "testsuite"
    secret = "letmein"

    user_id = "test_user_id"
    user_representation = "Test User"

    scopes = None
    heeft_alle_autorisaties = False
    zaaktype = None
    informatieobjecttype = None
    besluittype = None
    max_vertrouwelijkheidaanduiding = VertrouwelijkheidsAanduiding.zeer_geheim

    @staticmethod
    def _create_credentials(
        client_id: str,
        secret: str,
        heeft_alle_autorisaties: bool,
        max_vertrouwelijkheidaanduiding: str,
        scopes: Optional[List[str]] = None,
        zaaktype: Optional[str] = None,
        informatieobjecttype: Optional[str] = None,
        besluittype: Optional[str] = None,
    ):
        JWTSecret.objects.get_or_create(
            identifier=client_id, defaults={"secret": secret}
        )

        config = AuthorizationsConfig.get_solo()

        applicatie = Applicatie.objects.create(
            client_ids=[client_id],
            label="for test",
            heeft_alle_autorisaties=heeft_alle_autorisaties,
        )

        if heeft_alle_autorisaties is False:
            autorisatie = Autorisatie.objects.create(
                applicatie=applicatie,
                component=config.component,
                scopes=scopes or [],
                zaaktype=zaaktype or "",
                informatieobjecttype=informatieobjecttype or "",
                besluittype=besluittype or "",
                max_vertrouwelijkheidaanduiding=max_vertrouwelijkheidaanduiding,
            )
        else:
            autorisatie = None

        return applicatie, autorisatie

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        applicatie, autorisatie = cls._create_credentials(
            cls.client_id,
            cls.secret,
            heeft_alle_autorisaties=cls.heeft_alle_autorisaties,
            scopes=cls.scopes,
            zaaktype=cls.zaaktype,
            informatieobjecttype=cls.informatieobjecttype,
            besluittype=cls.besluittype,
            max_vertrouwelijkheidaanduiding=cls.max_vertrouwelijkheidaanduiding,
        )
        cls.applicatie = applicatie
        cls.autorisatie = autorisatie

    def setUp(self):
        super().setUp()

        token = generate_jwt_auth(
            client_id=self.client_id,
            secret=self.secret,
            user_id=self.user_id,
            user_representation=self.user_representation,
        )
        self.client.credentials(HTTP_AUTHORIZATION=token)
