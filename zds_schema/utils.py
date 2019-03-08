import re
from typing import Union

from django.db import models
from django.http import HttpRequest
from django.urls import Resolver404, get_resolver

try:
    from djangorestframework_camel_case.util import underscore_to_camel as _underscore_to_camel
except ImportError:
    from djangorestframework_camel_case.util import underscoreToCamel as _underscore_to_camel

RE_UNDERSCORE = re.compile(r"[a-z]_[a-z]")


def lookup_kwargs_to_filters(lookup_kwargs: dict, kwargs: dict) -> dict:
    """
    Using the lookup_kwargs map and the view kwargs, construct the queryset
    filter dict.
    """
    filters = {}
    for kwarg, field_name in lookup_kwargs.items():
        if kwarg not in kwargs:
            continue
        filters[field_name] = kwargs[kwarg]
    return filters


def get_viewset_for_path(path: str) -> 'rest_framework.viewsets.ViewSet':
    """
    Look up which viewset matches a path.
    """
    # NOTE: this doesn't support setting a different urlconf on the request
    resolver = get_resolver()
    try:
        resolver_match = resolver.resolve(path)
    except Resolver404 as exc:
        raise models.ObjectDoesNotExist("URL did not resolve") from exc
    callback, callback_args, callback_kwargs = resolver_match

    assert hasattr(callback, 'cls'), "Callback doesn't appear to be from a viewset"

    viewset = callback.cls(**callback.initkwargs)
    viewset.action_map = callback.actions
    viewset.request = HttpRequest()
    viewset.args = callback_args
    viewset.kwargs = callback_kwargs

    return viewset


def get_resource_for_path(path: str) -> models.Model:
    """
    Retrieve the API instance belonging to a (detail) path.
    """
    viewset = get_viewset_for_path(path)

    # See rest_framework.mixins.RetieveModelMixin.get_object()
    lookup_url_kwarg = viewset.lookup_url_kwarg or viewset.lookup_field
    filter_kwargs = {viewset.lookup_field: viewset.kwargs[lookup_url_kwarg]}

    return viewset.get_queryset().get(**filter_kwargs)


def underscore_to_camel(input_: Union[str, int]) -> str:
    """
    Convert a string from under_score to camelCase.
    """
    if not isinstance(input_, str):
        return input_

    return re.sub(RE_UNDERSCORE, _underscore_to_camel, input_)
