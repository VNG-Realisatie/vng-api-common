from unittest.mock import patch

from django.urls import reverse

import pytest
from notifications_api_common.models import NotificationsConfig
from rest_framework import status


@pytest.mark.django_db
def test_config_view(api_client):
    """
    regression test for https://github.com/open-zaak/open-notificaties/issues/119
    """
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = None

    notifications_config.save()

    path = reverse("view-config")
    response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK
