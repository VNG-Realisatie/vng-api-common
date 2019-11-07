import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_unauthorized_jwtsecret_create_forbidden(settings):
    url = reverse("jwtsecret-create")
    client = APIClient()

    response = client.post(url, {"identifier": "foo", "secret": "bar"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
