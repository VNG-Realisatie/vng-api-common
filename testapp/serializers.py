from rest_framework import serializers
from testapp.models import Person

from vng_api_common.serializers import GegevensGroepSerializer


class AddressSerializer(GegevensGroepSerializer):
    class Meta:
        model = Person
        gegevensgroep = 'address'


class PersonSerializer(serializers.ModelSerializer):
    address = AddressSerializer(allow_null=True)

    class Meta:
        model = Person
        fields = ("address", "name")
