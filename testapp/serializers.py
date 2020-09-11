from rest_framework import serializers

from testapp.models import Group, Person
from vng_api_common.serializers import GegevensGroepSerializer


class AddressSerializer(GegevensGroepSerializer):
    class Meta:
        model = Person
        gegevensgroep = "address"


class PersonSerializer(serializers.ModelSerializer):
    address = AddressSerializer(allow_null=True)

    class Meta:
        model = Person
        fields = ("address", "name")


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
