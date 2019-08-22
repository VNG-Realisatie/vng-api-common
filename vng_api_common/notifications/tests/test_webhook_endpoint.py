from django.test import override_settings
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase

from vng_api_common.tests import JWTAuthMixin

from ..constants import SCOPE_NOTIFICATIES_PUBLICEREN_LABEL


@override_settings(ROOT_URLCONF="vng_api_common.notifications.tests.urls")
class WebhookTests(JWTAuthMixin, APITestCase):

    scopes = [SCOPE_NOTIFICATIES_PUBLICEREN_LABEL]
    url = reverse_lazy("notificaties-webhook")

    def test_auth_required(self):
        self.client.credentials()  # clear any credentials

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receive_nofication(self):
        data = {
            "kanaal": "zaken",
            "hoofdObject": "https://zaken-api.vng.cloud/api/v1/zaken/d7a22",
            "resource": "status",
            "resourceUrl": "https://zaken-api.vng.cloud/api/v1/statussen/d7a22/721c9",
            "actie": "create",
            "aanmaakdatum": "2018-01-01T17:00:00Z",
            "kenmerken": {
                "bron": "082096752011",
                "zaaktype": "https://example.com/api/v1/zaaktypen/5aa5c",
                "vertrouwelijkeidaanduiding": "openbaar",
            },
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
