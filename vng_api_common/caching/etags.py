"""
Calculate ETag values for API resources.
"""
import functools
import hashlib

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import Http404, HttpRequest

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.settings import api_settings

from ..serializers import GegevensGroepSerializer
from ..utils import get_resource_for_path, get_subclasses


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
    serializer_class = _get_serializer_for_models()[model_class]

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


@functools.lru_cache(maxsize=None)
def _get_serializer_for_models():
    """
    Map models to the serializer to use.

    If multiple serializers exist for a model, it must be explicitly defined.
    """
    model_serializers = {}
    for serializer_class in get_subclasses(serializers.ModelSerializer):
        if not hasattr(serializer_class, "Meta"):
            continue

        if issubclass(serializer_class, GegevensGroepSerializer):
            continue

        model = serializer_class.Meta.model
        if model in model_serializers:
            continue

        model_serializers[model] = serializer_class
    return model_serializers
