"""
Signals listen to changes in models using ETagMixin and models related to those.

A changed m2m for example may affect the output of the ETag.

The signal does nothing except clearing the calculated value, which will be
re-calculated on the next fetch.
"""
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.db.models.signals import m2m_changed, post_save
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


@receiver(post_save)
def schedule_etag_clearing(sender: ModelBase, instance: models.Model, **kwargs):
    if kwargs["raw"]:
        return

    if not is_etag_model(sender):
        return

    # no value set for the ETag, nothing to do
    if not instance._etag:
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
    if action not in ["post_add", "post_clear", "post_remove"]:
        return

    if not is_etag_model(model):
        return

    if is_etag_model(type(instance)):
        _schedule_clear_etag(instance)

    instances = model.objects.filter(pk__in=kwargs["pk_set"])
    for instance in instances:
        _schedule_clear_etag(instance)
