from django.urls import include, path

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from test_serializer_extensions import PolySerializer

from testapp.models import FkModel
from vng_api_common import routers
from vng_api_common.generators import OpenAPISchemaGenerator


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


def _generate_schema():
    generator = OpenAPISchemaGenerator(
        patterns=urlpatterns,
    )
    return generator.get_schema()


def test_camilize():
    schema = _generate_schema()
    parameters = schema["paths"]["/api/camilize"]["get"]["parameters"]

    assert parameters[0]["name"] == "fieldWithUnderscores"
    assert parameters[1]["name"] == "name"
    assert parameters[2]["name"] == "poly__name"
