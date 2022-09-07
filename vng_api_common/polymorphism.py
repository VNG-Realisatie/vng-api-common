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
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent

from rest_framework import serializers

from vng_api_common.utils import underscore_to_camel

__all__ = ["Discriminator", "PolymorphicSerializer"]

logger = logging.getLogger(__name__)


class Discriminator:
    def __init__(
        self,
        discriminator_field: str,
        mapping: Dict[Any, Union[tuple, serializers.ModelSerializer]],
        group_field: Union[None, str] = None,
        same_model: bool = True,
    ):
        self.discriminator_field = discriminator_field
        self.mapping = mapping
        self.group_field = group_field
        self.same_model = same_model

    def to_representation(self, instance) -> OrderedDict:
        discriminator_value = getattr(instance, self.discriminator_field)
        serializer = self.mapping.get(discriminator_value)
        if serializer is None:
            return None

        representation = serializer.to_representation(instance)
        return representation

    def to_internal_value(self, data) -> OrderedDict:
        discriminator_value = data[self.discriminator_field]
        serializer = self.mapping.get(discriminator_value)
        if serializer is None:
            return None

        internal_value = serializer.to_internal_value(data)
        # if nested serializer was generated in _sanitize_discriminator name if group_field
        # was changed in the internal_value. We need to return it
        if (
            self.group_field
            and self.group_field not in internal_value
            and len(internal_value) == 1
        ):
            key, value = internal_value.popitem()
            internal_value = OrderedDict({self.group_field: value})

        return internal_value


class PolymorphicSerializerMetaclass(serializers.SerializerMetaclass):
    @classmethod
    def _sanitize_discriminator(cls, name, attrs) -> Union[Discriminator, None]:
        discriminator = attrs["discriminator"]
        if discriminator is None:
            return None

        model = attrs["Meta"].model

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

                Meta = type("Meta", (), {"model": model, "fields": tuple(fields)})
                serializer_class = type(
                    name, (serializers.ModelSerializer,),
                    {"Meta": Meta,}
                )

                discriminator.mapping[value] = serializer_class()

            values_seen.add(value)

            serializer = discriminator.mapping[value]

            if serializer is None:
                continue

            # rewrite it to nested serializer
            if discriminator.group_field:
                group_name = (
                    f"{discriminator.group_field}_{serializer.__class__.__name__}"
                )
                group_meta = type(
                    "Meta", (), {"model": model, "fields": (discriminator.group_field,)}
                )

                # find source field for nested serializer
                source = None
                related_fields = model._meta.fields_map
                for field_name, field_type in related_fields.items():
                    if field_type.related_model == serializer.Meta.model:
                        source = field_name

                group_field = serializer.__class__(
                    source=source, required=False, label=discriminator.group_field
                )

                group_serializer_class = type(
                    group_name,
                    (serializers.ModelSerializer,),
                    {"Meta": group_meta, discriminator.group_field: group_field},
                )
                discriminator.mapping[value] = group_serializer_class()

        if field.choices:
            values = {choice[0] for choice in field.choices}
            difference = values - values_seen
            if difference:
                logger.warning(
                    "'%s': not all possible values map to a serializer. Missing %s",
                    name,
                    difference,
                )
        return discriminator

    def __new__(cls, name, bases, attrs):
        attrs["discriminator"] = cls._sanitize_discriminator(name, attrs)
        return super().__new__(cls, name, bases, attrs)


class PolymorphicSerializer(
    serializers.HyperlinkedModelSerializer, metaclass=PolymorphicSerializerMetaclass
):
    discriminator: Discriminator = None

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


class PolymorphicSerializerExtension(OpenApiSerializerExtension):
    target_class = "vng_api_common.polymorphism.PolymorphicSerializer"
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        serializer = self.target
        schema = auto_schema._map_basic_serializer(serializer, direction)
        root_component = auto_schema.resolve_serializer(serializer, direction)

        for attr, model_serializer in serializer.discriminator.mapping.items():
            linked_schema = {"allOf": [root_component.ref]}

            if model_serializer:
                component = auto_schema.resolve_serializer(model_serializer, direction)

                if component:
                    linked_schema["allOf"].append(component.ref)

            linked_component = ResolvedComponent(
                name=attr, type=ResolvedComponent.SCHEMA, schema=linked_schema
            )
            auto_schema.registry.register_on_missing(linked_component)

        polymorphic_schema = {
            "discriminator": {
                "propertyName": underscore_to_camel(
                    serializer.discriminator.discriminator_field
                )
            }
        }

        return {**schema, **polymorphic_schema}
