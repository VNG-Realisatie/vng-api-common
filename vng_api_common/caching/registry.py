import logging
from dataclasses import dataclass
from typing import Dict, Iterable, Set, Type, Union

from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields.related import RelatedField as _RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel

from rest_framework.relations import (
    HyperlinkedIdentityField,
    ManyRelatedField,
    RelatedField,
)
from rest_framework.schemas.generators import BaseSchemaGenerator
from rest_framework.serializers import Serializer
from rest_framework.utils.model_meta import get_field_info

logger = logging.getLogger(__name__)

RelatedModelField = Union[_RelatedField, ForeignObjectRel]


DEPENDENCY_REGISTRY: Dict[ModelBase, Set["Dependency"]] = {}
"""
Module global to track which models affect which resources through which relation.

A write (create, update, delete, m2m_changed) of any of the models in the keys of the
dependency affects the models referenced in the dependencies (values of the dependency
data structure). The values are sets of dependencies wrapping around django model fields,
which now their accessor name and which model they belong to.

This way, you can express that a model "ZAAK" with a OneToOneField "RESULTAAT" is
(potentially) affected by changes in the related resultaat model.
"""

MODEL_SERIALIZERS: Dict[ModelBase, Type[Serializer]] = {}
"""
Module global to track which serializer is used for a given model for ETag calculation.

This is extracted from the viewset declaration and explicitly connects model and
serializer class, in the event that multiple (sub)serializers are used for a given model.
"""


@dataclass
class Dependency:
    field: Union[ForeignObjectRel, RelatedModelField]

    @property
    def source_model(self) -> ModelBase:
        return self.field.related_model

    @property
    def affected_model(self) -> ModelBase:
        return self.field.model

    def __hash__(self):
        return hash(self.field)

    def get_related_objects(self, instance: models.Model) -> Iterable[models.Model]:
        assert isinstance(
            instance, self.source_model
        ), "Instance is not of expected model class"

        reverse_relation_field = self.field.remote_field

        try:
            if isinstance(reverse_relation_field, ForeignObjectRel):
                query_like = getattr(
                    instance, reverse_relation_field.get_accessor_name()
                )
            else:
                query_like = getattr(instance, reverse_relation_field.name)
        except ObjectDoesNotExist:  # nullable OneToOneField, for example
            return []

        # reverse FK or m2m
        if isinstance(query_like, (models.Manager, models.QuerySet)):
            related_objects = query_like.all()
        # one-to-one field or FK
        else:
            related_objects = [query_like] if query_like is not None else []

        return related_objects


def extract_dependencies(viewset: type, explicit_field_names: Set[str]) -> None:
    """
    Introspect the viewset class and add the dependencies to the registry if needed.
    """
    # figure out the viewset model
    model = viewset.queryset.model

    # validate the explicit field names
    if explicit_field_names:
        all_field_names = {field.name for field in model._meta.get_fields()}
        incorrect = explicit_field_names - all_field_names
        if incorrect:
            raise ValueError(
                f"The field names {', '.join(incorrect)} could not be found on the model {model}"
            )

    # next, introspect the serialier
    generator = BaseSchemaGenerator()
    callback = viewset.as_view({"get": "retrieve"})
    view = generator.create_view(callback, method="GET", request=None)
    serializer = view.get_serializer()

    if model in MODEL_SERIALIZERS:
        logger.warning("Model %r is already registered in MODEL_SERIALIZERS.", model)
    else:
        MODEL_SERIALIZERS[model] = type(serializer)

    info = get_field_info(model)
    (
        pk,
        fields,
        forward_relations,
        reverse_relations,
        fields_and_pk,
        relationships,
    ) = info

    for field in serializer.fields.values():
        if not isinstance(field, (RelatedField, ManyRelatedField)):
            continue

        # HyperlinkedIdentityField points to the object itself and not a related object
        if isinstance(field, HyperlinkedIdentityField):
            continue

        if field.source not in relationships:
            logger.debug(
                "Field source %s not found in relationships, skipping", field.source
            )
            continue

        try:
            model_field = model._meta.get_field(field.source)
        except FieldDoesNotExist:
            relation_info = relationships[field.source]
            assert relation_info.to_many
            # find the field by accessor name
            candidates = [
                f
                for f in model._meta.get_fields()
                if f.remote_field
                and getattr(f, "get_accessor_name", None)
                and f.get_accessor_name() == field.source
            ]
            assert len(candidates) == 1
            model_field = candidates[0]

        add_dependency(model_field)

    # and finally, add the explicit field names
    for model_field_name in explicit_field_names:
        model_field = model._meta.get_field(model_field_name)
        add_dependency(model_field)


def add_dependency(model_field: RelatedModelField) -> None:
    dependency = Dependency(field=model_field)

    source_model = dependency.source_model
    if source_model not in DEPENDENCY_REGISTRY:
        DEPENDENCY_REGISTRY[source_model] = set()

    DEPENDENCY_REGISTRY[source_model].add(dependency)
