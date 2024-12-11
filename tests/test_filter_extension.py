from django.urls import include, path

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets

from testapp.models import FkModel
from testapp.serializers import PolySerializer
from tests import generate_schema
from vng_api_common import routers


class FkModelSerializer(serializers.ModelSerializer):
    poly = PolySerializer(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = FkModel
        fields = ("name", "poly")


class FkModelViewSet(viewsets.ModelViewSet):
    """Iets dat of iemand die voor de gemeente werkzaamheden uitvoert."""

    queryset = FkModel.objects.all()
    serializer_class = FkModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "name",
        "field_with_underscores",
        "poly__name",
    ]


app_name = "filter_extensions"

router = routers.DefaultRouter(trailing_slash=False)
router.register("camilize", FkModelViewSet, basename="filter_extensions_camilize")


urlpatterns = [
    path("api/", include(router.urls)),
]


def test_camilize():
    schema = generate_schema(urlpatterns)
    parameters = schema["paths"]["/api/camilize"]["get"]["parameters"]

    assert parameters[0]["name"] == "fieldWithUnderscores"
    assert parameters[1]["name"] == "name"
    assert parameters[2]["name"] == "poly__name"
