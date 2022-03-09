from typing import List
from unittest.mock import patch

from django.db.models import ObjectDoesNotExist
from django.utils.translation import gettext as _

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from vng_api_common.authorizations.models import Applicatie, Autorisatie
from vng_api_common.constants import ComponentTypes
from vng_api_common.middleware import JWTAuth
from vng_api_common.permissions import BaseAuthRequired
from vng_api_common.scopes import Scope
from vng_api_common.tests import generate_jwt_auth


class Permissions(BaseAuthRequired):
    obj_path = "some_fk"


class View(APIView):
    permission_classes = (Permissions,)
    action = "create"
    required_scopes = {"create": "dummy"}

    def post(self, request, *args, **kwargs):
        raise NotImplementedError


def test_failed_db_lookup():
    factory = APIRequestFactory()
    request = factory.post(
        "/foo", {"someFk": "https://example.com/api/v1/bar"}, format="json"
    )

    with patch("vng_api_common.permissions.BaseAuthRequired._get_obj") as m:
        m.side_effect = ObjectDoesNotExist("not found in DB")

        response = View.as_view()(request)

    assert response.status_code == 400
    invalid_params = response.data["invalid_params"][0]
    assert invalid_params == {
        "name": "someFk",
        "code": "object-does-not-exist",
        "reason": _("The object does not exist in the database"),
    }


class DummyView(APIView):
    permission_classes = (BaseAuthRequired,)
    required_scopes = {"post": Scope("dummy", private=True)}

    def post(self, request):
        return Response({})


class Auth(JWTAuth):
    def __init__(self, scopes: List[str]):
        self._scopes = scopes

    @property
    def applicaties(self):
        app = Applicatie.objects.create(client_ids=["dummy"])
        Autorisatie.objects.create(
            applicatie=app, component=ComponentTypes.zrc, scopes=self._scopes
        )
        return Applicatie.objects.filter(id=app.id)


@pytest.mark.django_db
class TestMethodPermissions:
    """
    Test that it's possible to define permissions on HTTP methods.
    """

    def _request(self, scopes: List[str]) -> Response:
        auth = generate_jwt_auth("dummy", "dummy")

        factory = APIRequestFactory()
        request = factory.post("/foo", {}, format="json", HTTP_AUTHORIZATION=auth)
        request.jwt_auth = Auth(scopes)
        return DummyView.as_view()(request)

    def test_post_not_allowed(self):
        response = self._request([])

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_allowed(self):
        response = self._request(["dummy"])

        assert response.status_code == status.HTTP_200_OK
