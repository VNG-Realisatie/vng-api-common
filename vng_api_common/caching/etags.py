"""
Calculate ETag values for API resources.
"""
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.http import Http404, HttpRequest

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework.request import Request
from rest_framework.settings import api_settings

from ..utils import get_resource_for_path
from .registry import MODEL_SERIALIZERS

logger = logging.getLogger(__name__)


class StaticRequest(HttpRequest):
    def get_host(self) -> str:
        site = Site.objects.get_current()
        return site.domain

    def _get_scheme(self) -> str:
        return "https" if settings.IS_HTTPS else "http"


def calculate_etag(instance: models.Model) -> str:
    """
    Calculate the MD5 hash of a resource representation in the API.

    The serializer for the model class is retrieved, and then used to construct
    the representation of the instance. Then, the representation is rendered
    to camelCase JSON, after which the MD5 hash is calculated of this result.
    """
    model_class = type(instance)
    serializer_class = MODEL_SERIALIZERS[model_class]

    # build a dummy request with the configured domain, since we're doing STRONG
    # comparison. Required as context for hyperlinked serializers
    request = Request(StaticRequest())
    request.version = api_settings.DEFAULT_VERSION
    request.versioning_scheme = api_settings.DEFAULT_VERSIONING_CLASS()

    serializer = serializer_class(instance=instance, context={"request": request})

    # render the output to json, which is used as hash input
    renderer = CamelCaseJSONRenderer()
    rendered = renderer.render(serializer.data, "application/json")

    # calculate md5 hash
    return hashlib.md5(rendered).hexdigest()


def etag_func(request: HttpRequest, etag_field: str = "_etag", **view_kwargs):
    try:
        obj = get_resource_for_path(request.path)
    except ObjectDoesNotExist:
        raise Http404
    etag_value = getattr(obj, etag_field)
    if not etag_value:  # calculate missing value and store it
        etag_value = obj.calculate_etag_value()
    return etag_value


@dataclass
class MethodCallback:
    callback: callable

    def __eq__(self, other):
        # NOTE: before Python 3.7 you could compare bound methods, as method.__eq__(other_method)
        # apparently compared the underlying data through __eq__. Dataclasses implement
        # __eq__ based on the fields from the constructor, in our case this is the Django
        # model instance. Django model instances in turn have __eq__ implemented to look
        # at the same type & if the pk is the same or not.
        # So, multiple instances of this class for the same django model instance will
        # have equal methods, and we can de-duplicate them using that logic.
        #
        # Since Python 3.7 this appears to no longer be the case, so we wrap it in our
        # own dataclass to perform this comparison
        if type(self) != type(other):  # noqa
            return False

        # same function object?
        if self.callback.__func__ != other.callback.__func__:
            return False

        # finally, compare the bound arguments
        return self.callback.__self__ == other.callback.__self__

    def __call__(self):
        return self.callback()


@dataclass
class EtagUpdate:
    instance: models.Model
    using: Optional[str] = None

    @classmethod
    def mark_affected(cls, obj: models.Model, using=None) -> None:
        """
        Schedule the ``instance`` to have it's ETag value updated on transaction commit.
        """
        already_updating = getattr(obj, "_updating_etag", False)
        if already_updating:
            return

        etag_update = cls(instance=obj, using=using)

        # we do not use the top-level transaction.commit, but need the underlying
        # connection object to ensure the update is only scheduled once.
        connection = transaction.get_connection(using)

        func = MethodCallback(etag_update.calculate_new_value)
        for _, _func in connection.run_on_commit:
            if func == _func:
                logger.debug(
                    "Update for model instance %r with pk %s was already scheduled",
                    type(obj),
                    obj.pk,
                )
                return

        logger.debug(
            "Scheduling model instance %r with pk %s for ETag update", type(obj), obj.pk
        )
        connection.on_commit(func)

    def calculate_new_value(self):
        with transaction.atomic(using=self.using):  # wrap in its own transaction
            # check if the record still exists - it may have been deleted as part of a
            # cascade delete, in which case we can't re-calculate and save anything.
            try:
                self.instance.refresh_from_db()
            except self.instance.DoesNotExist:
                return

            # track the actions _inside_ the on_commit handler, to prevent infinite
            # loops/stack overflows
            self.instance._updating_etag = True
            self.instance.calculate_etag_value()
            del self.instance._updating_etag
