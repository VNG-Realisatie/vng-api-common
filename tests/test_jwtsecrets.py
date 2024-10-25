import time

import jwt
import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from vng_api_common.authorizations.models import Applicatie, Autorisatie
from vng_api_common.constants import ComponentTypes
from vng_api_common.models import JWTSecret

JWT_ALG = "HS256"


def get_auth_headers(
    client_id: str,
    client_secret: str,
    user_id: str = "",
    user_representation: str = "",
    **claims,
) -> dict:
    payload = {
        # standard claims
        "iss": client_id,
        "iat": int(time.time()),
        # custom claims
        "client_id": client_id,
        "user_id": user_id,
        "user_representation": user_representation,
        **claims,
    }

    encoded = jwt.encode(payload, client_secret, algorithm=JWT_ALG)

    return {"Authorization": "Bearer {encoded}".format(encoded=encoded)}


@pytest.mark.django_db
def test_unauthorized_jwtsecret_create_forbidden():
    url = reverse("jwtsecret-create")
    client = APIClient()

    response = client.post(url, {"identifier": "foo", "secret": "bar"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_authorized_jwtsecret_create_ok():
    url = reverse("jwtsecret-create")
    client = APIClient()
    # set up auth
    JWTSecret.objects.create(identifier="pytest", secret="sekrit")
    app = Applicatie.objects.create(client_ids=["pytest"], label="tests")
    Autorisatie.objects.create(
        applicatie=app,
        component=ComponentTypes.ac,
        scopes=["autorisaties.credentials-registreren"],
    )
    auth_headers = get_auth_headers("pytest", "sekrit")
    client.credentials(HTTP_AUTHORIZATION=auth_headers["Authorization"])

    response = client.post(url, {"identifier": "foo", "secret": "bar"})

    assert response.status_code == status.HTTP_201_CREATED
