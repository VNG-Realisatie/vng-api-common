"""
Signals listen to changes in models using ETagMixin and models related to those.

A changed m2m for example may affect the output of the ETag.

The signal does nothing except clearing the calculated value, which will be
re-calculated on the next fetch.
"""
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.db.models.fields.related import ManyToOneRel
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver


def clear_etag(instance: models.Model):
    """
    Clear the value of the ETag field.
    """
    instance._etag = ""
    instance.save(update_fields=["_etag"])


def _schedule_clear_etag(instance: models.Model):
    transaction.on_commit(lambda: clear_etag(instance))


def is_etag_model(model: ModelBase) -> bool:
    try:
        model._meta.get_field("_etag")
    # model doesn't support ETags, nothing to do
    except FieldDoesNotExist:
        return False

    return True


def handle_related_etag_instances(instance: models.Model):
    model = type(instance)
    fields = [
        field
        for field in model._meta.get_fields()
        if field.is_relation and isinstance(field, ManyToOneRel)
    ]

    for field in fields:
        source_model = field.remote_field.model
        if not is_etag_model(source_model):
            continue  # TODO: what with more deeply nested objects?

        related_instances = getattr(instance, field.get_accessor_name()).all()
        for related_instance in related_instances:
            _schedule_clear_etag(related_instance)


def handle_m2m_cleared(
    sender: ModelBase, instance: models.Model, model: ModelBase
) -> None:
    """
    Clear the etag on the remote side of a m2m_field.clear()
    """
    # figure out which field is involved
    m2m_fields = [
        field
        for field in instance._meta.get_fields()
        if getattr(field, "related_model") is model
        and field.remote_field.through is sender
    ]
    assert len(m2m_fields) == 1, "This should resolve to a single m2m field"
    m2m_field = m2m_fields[0]

    qs = getattr(instance, m2m_field.name).all()
    for instance in qs:
        _schedule_clear_etag(instance)


@receiver([post_save, post_delete])
def schedule_etag_clearing(sender: ModelBase, instance: models.Model, **kwargs):
    if kwargs.get("raw"):
        return

    if not is_etag_model(sender):
        handle_related_etag_instances(instance)
        return

    # no value set for the ETag, nothing to do
    if not instance._etag:
        return

    if "update_fields" not in kwargs:
        return

    # only updating the _etag field - either to clear it, or to set the computed
    # value
    if kwargs["update_fields"] == {"_etag"}:
        return

    # clear existing value
    _schedule_clear_etag(instance)


@receiver(m2m_changed)
def schedule_etag_clearing_m2m(
    sender: ModelBase, instance: models.Model, action: str, model: ModelBase, **kwargs
):
    if action == "pre_clear":
        handle_m2m_cleared(sender, instance, model)
        return

    if action not in ["post_add", "post_clear", "post_remove"]:
        return

    if not is_etag_model(model):
        return

    if is_etag_model(type(instance)):
        _schedule_clear_etag(instance)

    pk_set = kwargs["pk_set"] or ()
    instances = model.objects.filter(pk__in=pk_set)
    for instance in instances:
        _schedule_clear_etag(instance)
