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

from .models import ETagMixin


def clear_etag(instance: models.Model):
    """
    Clear the value of the ETag field.
    """
    instance._etag = ""
    instance.save(update_fields=["_etag"])


@receiver(post_save)
def schedule_etag_clearing(sender: ModelBase, instance: models.Model, **kwargs):
    if kwargs["raw"]:
        return

    try:
        sender._meta.get_field("_etag")
    # model doesn't support ETags, nothing to do
    except FieldDoesNotExist:
        return

    if not instance._etag:
        return

    transaction.on_commit(lambda: clear_etag(instance))
