import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from zds_client.auth import ClientAuth

from vng_api_common.authorizations.models import Applicatie, Autorisatie
from vng_api_common.constants import ComponentTypes
from vng_api_common.models import JWTSecret


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
    auth = ClientAuth(client_id="pytest", secret="sekrit").credentials()[
        "Authorization"
    ]
    client.credentials(HTTP_AUTHORIZATION=auth)

    response = client.post(url, {"identifier": "foo", "secret": "bar"})

    assert response.status_code == status.HTTP_201_CREATED
