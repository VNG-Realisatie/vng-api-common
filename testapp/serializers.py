from drf_extra_fields.fields import Base64FileField
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from testapp.models import (
    GeometryModel,
    Group,
    Hobby,
    MediaFileModel,
    Person,
    Poly,
    PolyChoice,
    Record,
)
from vng_api_common.polymorphism import Discriminator, PolymorphicSerializer
from vng_api_common.serializers import GegevensGroepSerializer


class AddressSerializer(GegevensGroepSerializer):
    class Meta:
        model = Person
        gegevensgroep = "address"


class PersonSerializer(serializers.ModelSerializer):
    address = AddressSerializer(allow_null=True)
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ("address", "name", "group_name")

    def get_group_name(self, obj) -> str:
        return obj.group.name if obj.group_id else ""


class PersonSerializer2(serializers.ModelSerializer):
    address = AddressSerializer(allow_null=True, required=False)

    class Meta:
        model = Person
        fields = ("address", "name")


class GroupSerializer(serializers.ModelSerializer):
    person = PersonSerializer(many=True)

    class Meta:
        model = Group
        fields = ("person",)


class MediaFileModelSerializer(serializers.ModelSerializer):
    file = Base64FileField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MediaFileModel
        fields = ("file",)


class GeometryModelSerializer(serializers.ModelSerializer):
    geometry = GeometryField(required=False)

    class Meta:
        model = GeometryModel
        fields = ("geometry",)


# polymorphic serializer
class HobbySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hobby
        fields = ("name", "people")


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
