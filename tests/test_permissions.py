from unittest.mock import patch

from django.db.models import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from vng_api_common.permissions import BaseAuthRequired


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
