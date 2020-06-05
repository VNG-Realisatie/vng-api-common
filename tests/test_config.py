from django.test import override_settings

import pytest

from vng_api_common.notifications.models import NotificationsConfig


@pytest.mark.django_db
@override_settings(CUSTOM_CLIENT_FETCHER="testapp.utils.get_client")
def test_notificationsconfig_custom_client():
    config = NotificationsConfig.get_solo()
    client = config.get_client()
    assert client == "testclient"
