"""
Implement polymorphism at the API level.

Add support to DRF serializers for polymorphic resources. Polymorphic resources
take a certain shape depending on the value of a field, called the
discriminator. The model itself does not need to be made polymorphic, allowing
database queries to remain performant.

Usage:

>>> from vng_api_common.polymorphism import Discriminator, PolymorphicSerializer
>>> class AutorisatieBaseSerializer(PolymorphicSerializer):
...     discriminator = Discriminator(
...         discriminator_field='type',
...         mapping={
...             'value1': (
...                 'field_for_value1',
...             ),
...             'value2': (
...                 'field_for_value2',
...             ),
...         }
...     )
...
...     class Meta:
...         model = SomeModel
...         fields = (
...             'type',
...             'common_field',
...         )
...

The serializer output will then either contain ``field_for_value2`` or
``field_for_value2``, depending on the value of the field ``type``.
"""
import logging
from collections import OrderedDict
from typing import Any, Dict, Union

from django.core.exceptions import FieldDoesNotExist

from rest_framework import serializers

__all__ = ["Discriminator", "PolymorphicSerializer"]

logger = logging.getLogger(__name__)


class Discriminator:
    def __init__(self, discriminator_field: str, mapping: Dict[Any, Union[tuple, serializers.ModelSerializer]]):
        self.discriminator_field = discriminator_field
        self.mapping = mapping

    def to_representation(self, instance) -> OrderedDict:
        discriminator_value = getattr(instance, self.discriminator_field)
        serializer = self.mapping.get(discriminator_value)
        if serializer is None:
            return None
        return serializer.to_representation(instance)

    def to_internal_value(self, data) -> OrderedDict:
        discriminator_value = data.get(self.discriminator_field, '')
        if not discriminator_value:
            discriminator_value = getattr(self.instance, self.discriminator_field)
        serializer = self.mapping.get(discriminator_value)
        if serializer is None:
            return None
        return serializer.to_internal_value(data)


class PolymorphicSerializerMetaclass(serializers.SerializerMetaclass):

    @classmethod
    def _sanitize_discriminator(cls, name, attrs) -> Union[Discriminator, None]:
        discriminator = attrs['discriminator']
        if discriminator is None:
            return None

        model = attrs['Meta'].model

        try:
            field = model._meta.get_field(discriminator.discriminator_field)
        except FieldDoesNotExist as exc:
            raise FieldDoesNotExist(
                f"The discriminator field '{discriminator.discriminator_field}' "
                f"does not exist on the model '{model._meta.label}'"
            ) from exc

        values_seen = set()

        for value, fields in discriminator.mapping.items():
            # construct a serializer instance if a tuple/list of fields is passed
            if isinstance(fields, (tuple, list)):
                name = f"{value}{model._meta.object_name}Serializer"

                Meta = type('Meta', (), {
                    'model': model,
                    'fields': tuple(fields),
                })

                serializer_class = type(
                    name,
                    (serializers.ModelSerializer,),
                    {'Meta': Meta}
                )

                discriminator.mapping[value] = serializer_class()

            values_seen.add(value)

        if field.choices:
            values = {choice[0] for choice in field.choices}
            difference = values - values_seen
            if difference:
                logger.warn(
                    "'%s': not all possible values map to a serializer. Missing %s",
                    name, difference
                )

        return discriminator

    def __new__(cls, name, bases, attrs):
        attrs['discriminator'] = cls._sanitize_discriminator(name, attrs)
        return super().__new__(cls, name, bases, attrs)


class PolymorphicSerializer(serializers.HyperlinkedModelSerializer, metaclass=PolymorphicSerializerMetaclass):
    discriminator: Discriminator = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args:
            self.discriminator.instance = args[0]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        extra_fields = self.discriminator.to_representation(instance)
        if extra_fields:
            representation.update(extra_fields)
        return representation

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        extra_fields = self.discriminator.to_internal_value(data)
        if extra_fields:
            internal_value.update(extra_fields)
        return internal_value
