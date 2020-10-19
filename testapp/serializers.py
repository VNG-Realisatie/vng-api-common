from rest_framework import serializers

from testapp.models import Group, Hobby, Person
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


class HobbySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hobby
        fields = ("name", "people")
