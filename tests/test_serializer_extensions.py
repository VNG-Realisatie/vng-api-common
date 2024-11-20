from django.urls import include, path

from rest_framework import serializers, viewsets

from testapp.models import Group, Poly, PolyChoice, Record
from testapp.serializers import HobbySerializer
from tests import generate_schema
from vng_api_common import routers
from vng_api_common.polymorphism import Discriminator, PolymorphicSerializer
from vng_api_common.serializers import GegevensGroepSerializer, NestedGegevensGroepMixin


class SubgroupSerializer(GegevensGroepSerializer):
    class Meta:
        model = Group
        gegevensgroep = "subgroup"


class GroupSerializer(NestedGegevensGroepMixin, serializers.ModelSerializer):
    subgroup = SubgroupSerializer(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Group
        fields = (
            "name",
            "subgroup",
        )


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ("identificatie", "create_date")


class PolySerializer(PolymorphicSerializer):
    discriminator = Discriminator(
        discriminator_field="choice",
        mapping={
            PolyChoice.hobby: HobbySerializer(),
            PolyChoice.record: RecordSerializer(),
        },
        group_field="poly",
    )

    class Meta:
        model = Poly
        fields = ("name",)


class GroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class PolyView(viewsets.ModelViewSet):
    queryset = Poly.objects.all()
    serializer_class = PolySerializer


app_name = "serializer_extensions"

router = routers.DefaultRouter(trailing_slash=False)
router.register("group", GroupView, basename="serializer_extensions_group")
router.register("poly", PolyView, basename="serializer_extensions_poly")

urlpatterns = [
    path("api/", include(router.urls)),
]


def _generate_schema():
    return generate_schema(urlpatterns)


def test_gegevensgroup():
    schema = _generate_schema()
    gegevensgroup_path = schema["components"]["schemas"]["Subgroup"]

    assert "description" not in gegevensgroup_path
    assert gegevensgroup_path["type"] == "object"
    assert list(gegevensgroup_path["properties"].keys()) == ["field1", "field2"]
    assert gegevensgroup_path["required"] == ["field1"]


def test_polymorphic():
    schema = _generate_schema()
    gegevensgroup_path = schema["components"]["schemas"]["Poly"]
    hobby = "#/components/schemas/hobby_PolySerializer"
    record = "#/components/schemas/record_PolySerializer"

    assert "oneOf" in gegevensgroup_path
    assert gegevensgroup_path["oneOf"][0]["$ref"] == hobby
    assert gegevensgroup_path["oneOf"][1]["$ref"] == record

    assert "discriminator" in gegevensgroup_path
    assert gegevensgroup_path["discriminator"]["propertyName"] == "choice"
    assert gegevensgroup_path["discriminator"]["mapping"]["hobby"] == hobby
    assert gegevensgroup_path["discriminator"]["mapping"]["record"] == record
