from django.test import override_settings
from django.urls import reverse

import pytest
from rest_framework import status


@pytest.mark.django_db
@override_settings(CUSTOM_CLIENT_FETCHER="testapp.utils.get_client_with_auth")
def test_config_view(api_client):
    """
    regression test for https://github.com/open-zaak/open-notificaties/issues/119
    """
    path = reverse("view-config")

    response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK
