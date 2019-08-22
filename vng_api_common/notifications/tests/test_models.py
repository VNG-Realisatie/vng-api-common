from unittest import skipUnless
from unittest.mock import patch

from django.apps import apps
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from vng_api_common.tests import JWTAuthMixin

from ..constants import SCOPE_NOTIFICATIES_CONSUMEREN_LABEL
from ..models import NotificationsConfig, Subscription


@skipUnless(apps.is_installed("notifications.api"), "NRC API not enabled")
@override_settings(ROOT_URLCONF="vng_api_common.notifications.tests.urls")
class SubscriptionTests(JWTAuthMixin, APITestCase):

    scopes = [SCOPE_NOTIFICATIES_CONSUMEREN_LABEL]

    @classmethod
    def setUpTestData(cls):
        from notifications.datamodel.models import Kanaal

        super().setUpTestData()

        Kanaal.objects.create(naam="zaken")
        cls.config = NotificationsConfig.objects.create(
            api_root="http://testserver/api/"
        )

    @patch(
        "vng_api_common.notifications.models.Client.create",
        return_value={"url": "http://example.com/"},
    )
    def test_register_subscription(self, mock_create):
        url = reverse("abonnement-list", kwargs={"version": 1})
        sub = Subscription.objects.create(
            config=self.config,
            callback_url="http://testserver.com/api/callbacks",
            client_id="test",
            secret="test",
            channels=["zaken"],
        )

        sub.register()

        data = mock_create.call_args[1]["data"]

        # assert that we send valid data to the api

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
