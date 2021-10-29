from unittest.mock import patch

from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils.translation import ugettext as _

import pytest
from requests.exceptions import RequestException
from zds_client.client import ClientError

from vng_api_common.notifications.admin import register_webhook
from vng_api_common.notifications.models import NotificationsConfig, Subscription


@patch(
    "zds_client.client.Client.create",
    return_value={"url": "https://example.com/api/v1/abonnementen/1"},
)
@pytest.mark.django_db
def test_register_webhook_success(*mocks):
    request = RequestFactory().get("/")
    SessionMiddleware().process_request(request)
    MessageMiddleware().process_request(request)

    config = NotificationsConfig.get_solo()

    subscription = Subscription.objects.create(
        config=config,
        callback_url="https://example.com/callback",
        client_id="client_id",
        secret="secret",
        channels=["zaken"],
    )

    register_webhook(object, request, Subscription.objects.all())

    messages = list(get_messages(request))

    assert len(messages) == 0

    subscription.refresh_from_db()
    assert subscription._subscription == "https://example.com/api/v1/abonnementen/1"


@pytest.mark.django_db
def test_register_webhook_request_exception():
    request = RequestFactory().get("/")
    SessionMiddleware().process_request(request)
    MessageMiddleware().process_request(request)

    config = NotificationsConfig.get_solo()

    Subscription.objects.create(
        config=config,
        callback_url="https://example.com/callback",
        client_id="client_id",
        secret="secret",
        channels=["zaken"],
    )

    with patch(
        "zds_client.client.Client.create", side_effect=RequestException("exception")
    ):
        register_webhook(object, request, Subscription.objects.all())

    messages = list(get_messages(request))

    assert len(messages) == 1
    assert messages[0].message == _(
        "Something went wrong while registering subscription for {callback_url}: {e}"
    ).format(callback_url="https://example.com/callback", e="exception")


@pytest.mark.django_db
def test_register_webhook_client_error():
    request = RequestFactory().get("/")
    SessionMiddleware().process_request(request)
    MessageMiddleware().process_request(request)

    config = NotificationsConfig.get_solo()

    Subscription.objects.create(
        config=config,
        callback_url="https://example.com/callback",
        client_id="client_id",
        secret="secret",
        channels=["zaken"],
    )

    with patch("zds_client.client.Client.create", side_effect=ClientError("exception")):
        register_webhook(object, request, Subscription.objects.all())

    messages = list(get_messages(request))

    assert len(messages) == 1
    assert messages[0].message == _(
        "Something went wrong while registering subscription for {callback_url}: {e}"
    ).format(callback_url="https://example.com/callback", e="exception")
