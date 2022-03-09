"""
Test that server errors generate the appropriate JSON response.
"""
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView


class View(APIView):
    def get(self, *args, **kwargs):
        raise Exception("Unexpected")


def test_unexpected_exception():
    factory = APIRequestFactory()
    request = factory.get("/foo", format="json")

    response = View.as_view()(request)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"

    del response.data["instance"]
    assert response.data == {
        "type": "http://testserver/ref/fouten/APIException/",
        "code": "error",
        "title": _("A server error occurred."),
        "status": 500,
        "detail": "Internal Server Error",
    }
