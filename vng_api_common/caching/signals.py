"""
Signals listen to changes in models using ETagMixin and models related to those.

A changed m2m for example may affect the output of the ETag.

The signal does nothing except clearing the calculated value, which will be
re-calculated on the next fetch.
"""
from typing import Optional, Set

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .etags import EtagUpdate
from .registry import DEPENDENCY_REGISTRY, Dependency


def mark_affected_objects(
    dependencies: Optional[Set[Dependency]], instance: models.Model
):
    if dependencies is None:
        return

    for dependency in dependencies:
        if not is_etag_model(dependency.affected_model):
            continue

        for obj in dependency.get_related_objects(instance):
            EtagUpdate.mark_affected(obj)


@receiver([post_save, post_delete])
def mark_related_instances_for_etag_update(
    sender: ModelBase, instance: models.Model, **kwargs
) -> None:
    """
    Determine which instances are affected by changes in ``instance``.

    The sender/instance may be a model supporting ETag-based caching, or may be related
    to such a model. We must determine which instances are affected and ensure that
    the ETag value is properly scheduled for re-computation based on the new data.

    Processing of the ETag values is only done on transaction.on_commit so that all
    explicit changes are propagated before we even consider calculating the new ETag
    value.
    """
    if kwargs.get("raw"):
        return

    # prevent infinite recursion caused by the save of the new _etag value
    if kwargs.get("update_fields") == {"_etag"}:
        return

    # if the model is itself something that has an etag, mark it for update
    if is_etag_model(sender) and not kwargs["signal"] is post_delete:
        EtagUpdate.mark_affected(instance)

    # otherwise, find out which relations are affected
    dependency_for = DEPENDENCY_REGISTRY.get(sender)
    mark_affected_objects(dependency_for, instance)


@receiver(m2m_changed)
def mark_m2m_related_instances_for_etag_update(
    sender: ModelBase,
    instance: models.Model,
    action: str,
    model: ModelBase,
    **kwargs,
) -> None:
    """
    Determine which instances are affected by m2m changes.

    Similar to :func:`mark_related_instances_for_etag_update`, but then the m2m variant.
    """

    if action == "pre_clear":
        # instance is the instance whose m2m field is being cleared
        handle_m2m_cleared(sender, instance, model)
        return

    if action not in ["post_add", "post_clear", "post_remove"]:
        return

    # instance is the object's m2m field being changed
    if is_etag_model(type(instance)):
        EtagUpdate.mark_affected(instance)

    # involved objects on the "other side of the relationship"
    pk_set = kwargs["pk_set"] or ()
    instances = model._default_manager.filter(pk__in=pk_set)
    related_is_etag = is_etag_model(model)
    dependency_for = DEPENDENCY_REGISTRY.get(model)

    for related_instance in instances:
        if related_is_etag:
            EtagUpdate.mark_affected(related_instance)

        mark_affected_objects(dependency_for, related_instance)


def is_etag_model(model: ModelBase) -> bool:
    try:
        model._meta.get_field("_etag")
    # model doesn't support ETags, nothing to do
    except FieldDoesNotExist:
        return False

    return True


def handle_m2m_cleared(
    sender: ModelBase, instance: models.Model, model: ModelBase
) -> None:
    """
    Clear the etag on the remote side of a m2m_field.clear()
    """

    def _get_through(field):
        if hasattr(field, "through"):
            return field.through
        return field.remote_field.through

    # figure out which field is involved
    m2m_fields = [
        field
        for field in instance._meta.get_fields()
        if getattr(field, "related_model") is model and _get_through(field) is sender
    ]
    assert len(m2m_fields) == 1, "This should resolve to a single m2m field"
    m2m_field = m2m_fields[0]

    qs = getattr(instance, m2m_field.name).all()
    dependency_for = DEPENDENCY_REGISTRY.get(qs.model)

    for related_instance in qs:
        if is_etag_model(qs.model):
            EtagUpdate.mark_affected(related_instance)

        mark_affected_objects(dependency_for, related_instance)
