from rest_framework import status
from rest_framework.test import APITestCase

from vng_api_common.tests import JWTScopesMixin, reverse_lazy

from ..api.scopes import SCOPE_NOTIFICATIES_STUREN


class WebhookTests(JWTScopesMixin, APITestCase):

    scopes = [SCOPE_NOTIFICATIES_STUREN]
    url = reverse_lazy('notificaties-webhook')

    def test_auth_required(self):
        self.client.credentials()  # clear any credentials

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receive_nofication(self):
        data = {
            "kanaal": "zaken",
            "hoofdObject": "https://ref.tst.vng.cloud/zrc/api/v1/zaken/d7a22",
            "resource": "status",
            "resourceUrl": "https://ref.tst.vng.cloud/zrc/api/v1/statussen/d7a22/721c9",
            "actie": "create",
            "aanmaakdatum": "2018-01-01T17:00:00Z",
            "kenmerken": [
                {"bron": "082096752011"},
                {"zaaktype": "https://example.com/api/v1/zaaktypen/5aa5c"},
                {"vertrouwelijkeidaanduiding": "openbaar"}
            ]
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
