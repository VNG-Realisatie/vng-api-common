import logging
import re
import uuid
from typing import Union

from django.apps import apps
from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.urls import Resolver404, get_resolver
from django.utils.module_loading import import_string

from zds_client.client import ClientError

try:
    from djangorestframework_camel_case.util import underscore_to_camel as _underscore_to_camel
except ImportError:
    from djangorestframework_camel_case.util import underscoreToCamel as _underscore_to_camel


logger = logging.getLogger(__name__)

RE_UNDERSCORE = re.compile(r"[a-z]_[a-z]")


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass


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
    if settings.FORCE_SCRIPT_NAME and path.startswith(settings.FORCE_SCRIPT_NAME):
        path = path[len(settings.FORCE_SCRIPT_NAME):]

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


def get_uuid_from_path(path: str) -> str:
    """
    Get the last path of path
    """
    if path.endswith('/'):
        path = path.rstrip('/')

    uuid_str = path.rsplit('/')[-1]

    # validate if it's a proper hex string
    uuid.UUID(uuid_str)

    return uuid_str


def request_object_attribute(url: str, attribute: str, resource: Union[str, None] = None) -> str:
    from .models import APICredential
    Client = import_string(settings.ZDS_CLIENT_CLASS)
    client = Client.from_url(url)
    client.auth = APICredential.get_auth(url)
    try:
        result = client.retrieve(resource, url=url)[attribute]
    except (ClientError, KeyError) as exc:
        logger.warning("%s was retrieved from %s with the %s: %s", attribute, url, exc.__class__.__name__, exc)
        result = ''
    return result


def generate_unique_identification(instance: models.Model, date_field_name: str):
    model = type(instance)
    model_name = getattr(
        model,
        "IDENTIFICATIE_PREFIX",
        model._meta.model_name.upper()
    )

    year = getattr(instance, date_field_name).year
    prefix = f'{model_name}-{year}'

    pattern = prefix + r'-\d{10}'

    issued_ids_for_year = model._default_manager.filter(identificatie__regex=pattern)

    if issued_ids_for_year.exists():
        max_id = issued_ids_for_year.aggregate(models.Max('identificatie'))['identificatie__max']
        number = int(max_id.split('-')[-1]) + 1
    else:
        number = 1

    padded_number = str(number).zfill(10)
    return f'{prefix}-{padded_number}'


def get_help_text(model_string: str, field_name: str) -> str:
    ModelClass = apps.get_model(model_string, require_ready=False)
    field = ModelClass._meta.get_field(field_name)
    return field.help_text
