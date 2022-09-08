"""
Test that the required content type headers are present.
"""
from django.urls import path
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from vng_api_common.generators import OpenAPISchemaGenerator


class DummyView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        return Response({})

    def post(self, request):
        return Response({})


class JSONView(DummyView):
    parser_classes = (JSONParser,)


class MultiPartView(DummyView):
    parser_classes = (MultiPartParser,)


urlpatterns = [
    path("json", JSONView.as_view(), name="json"),
    path("multipart", MultiPartView.as_view(), name="multipart"),
]


def _generate_schema():
    generator = OpenAPISchemaGenerator(patterns=urlpatterns)
    return generator.get_schema()


def test_json_content_type():
    schema = _generate_schema()

    get_operation = schema.paths["/json"]["get"]
    post_operation = schema.paths["/json"]["post"]

    assert get_operation["parameters"] == []
    assert post_operation["parameters"] == [
        OpenApiParameter(
            name="Content-Type",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            required=True,
            enum=["application/json"],
            description=_("Content type of the request body."),
        )
    ]


def test_multipart_content_type():
    schema = _generate_schema()

    get_operation = schema.paths["/multipart"]["get"]
    post_operation = schema.paths["/multipart"]["post"]

    assert get_operation["parameters"] == []
    assert post_operation["parameters"] == [
        OpenApiParameter(
            name="Content-Type",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            required=True,
            enum=["multipart/form-data"],
            description=_("Content type of the request body."),
        )
    ]
