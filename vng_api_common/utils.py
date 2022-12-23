import logging
import re
import uuid
from typing import TYPE_CHECKING, List, Optional, Union

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpRequest
from django.urls import Resolver404, ResolverMatch, get_resolver, get_script_prefix
from django.utils.encoding import smart_str
from django.utils.module_loading import import_string

from rest_framework.utils import formatting
from zds_client.client import ClientError

from .client import get_client

try:
    from djangorestframework_camel_case.util import (
        underscore_to_camel as _underscore_to_camel,
    )
except ImportError:
    from djangorestframework_camel_case.util import (
        underscoreToCamel as _underscore_to_camel,
    )

if TYPE_CHECKING:
    from rest_framework.viewsets import ViewSet


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


class NotAViewSet(Exception):
    pass


def resolve_path(path: str, resolver=None, script_prefix=None) -> ResolverMatch:
    resolver = resolver or get_resolver()
    prefix = script_prefix or get_script_prefix()
    path = path.replace(prefix, "/", 1)
    try:
        return resolver.resolve(path)
    except Resolver404 as exc:
        raise models.ObjectDoesNotExist("URL did not resolve") from exc


def get_viewset_for_path(path: str, method="GET") -> "ViewSet":
    """
    Look up which viewset matches a path.
    """
    # NOTE: this doesn't support setting a different urlconf on the request
    callback, callback_args, callback_kwargs = resolve_path(path)

    if not hasattr(callback, "cls"):
        raise NotAViewSet(f"Callback for {path} does not look like a viewset")

    viewset = callback.cls(**callback.initkwargs)
    viewset.action_map = callback.actions
    viewset.request = HttpRequest()
    viewset.args = callback_args
    viewset.kwargs = callback_kwargs

    viewset.action = viewset.action_map.get(method.lower())

    return viewset


def get_resource_for_path(path: str) -> models.Model:
    """
    Retrieve the API instance belonging to a (detail) path.
    """
    if settings.FORCE_SCRIPT_NAME and path.startswith(settings.FORCE_SCRIPT_NAME):
        prefix_length = len(settings.FORCE_SCRIPT_NAME)
        path = path[prefix_length:]

    viewset = get_viewset_for_path(path)

    # See rest_framework.mixins.RetieveModelMixin.get_object()
    lookup_url_kwarg = viewset.lookup_url_kwarg or viewset.lookup_field
    filter_kwargs = {viewset.lookup_field: viewset.kwargs[lookup_url_kwarg]}

    return viewset.get_queryset().get(**filter_kwargs)


def get_resources_for_paths(paths: List[str]) -> Optional[models.QuerySet]:
    """
    Retrieve API instances belonging to a list of (detail) paths.

    This is the bulk version of :func:`vng_api_common.utils.get_resource_for_path`,
    which doesn't scale well when a lot of paths are involved. This replaces many
    queries with a single bulk query.

    .. warning::

        This means that all the resource paths must point to the same resource, as the
        viewset will only be fetched once from the first item and used to retrieve
        all the resources.

        This function compares the number of resolved instances vs the number of input
        paths, and if that is not equal, there's something off and a :class:`RuntimeError`
        is raised.
    """
    if not paths:
        return None

    # NOTE: this doesn't support setting a different urlconf on the request
    resolver = get_resolver()
    prefix = get_script_prefix()
    lookup_kwarg_values = []

    for path in paths:
        callback, callback_args, callback_kwargs = resolve_path(
            path,
            resolver=resolver,
            script_prefix=prefix,
        )

        if not hasattr(callback, "cls"):
            raise NotAViewSet(f"Callback for {path} does not look like a viewset")

        viewset_cls = callback.cls
        lookup_url_kwarg = viewset_cls.lookup_url_kwarg or viewset_cls.lookup_field
        lookup_kwarg_values.append(callback_kwargs[lookup_url_kwarg])

    queryset = viewset_cls().get_queryset()
    # drop any joins or prefetch_related to speed things up even more
    queryset = queryset.select_related(None).prefetch_related(None)

    filtered_queryset = queryset.filter(
        **{f"{viewset_cls.lookup_field}__in": lookup_kwarg_values}
    )
    if not len(filtered_queryset) == len(paths):
        raise RuntimeError(
            f"Some paths could not be resolved with viewset {viewset_cls} - are you sure "
            "that all paths point to the same resource?"
        )
    return filtered_queryset


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
    if path.endswith("/"):
        path = path.rstrip("/")

    uuid_str = path.rsplit("/")[-1]

    # validate if it's a proper hex string
    uuid.UUID(uuid_str)

    return uuid_str


def request_object_attribute(
    url: str, attribute: str, resource: Union[str, None] = None
) -> str:
    client = get_client(url)

    try:
        result = client.retrieve(resource, url=url)[attribute]
    except (ClientError, KeyError) as exc:
        logger.warning(
            "%s was retrieved from %s with the %s: %s",
            attribute,
            url,
            exc.__class__.__name__,
            exc,
        )
        result = ""
    return result


def generate_unique_identification(instance: models.Model, date_field_name: str):
    model = type(instance)
    model_name = getattr(model, "IDENTIFICATIE_PREFIX", model._meta.model_name.upper())

    year = getattr(instance, date_field_name).year
    prefix = f"{model_name}-{year}"

    pattern = prefix + r"-\d{10}"

    issued_ids_for_year = model._default_manager.filter(identificatie__regex=pattern)

    if issued_ids_for_year.exists():
        max_id = issued_ids_for_year.aggregate(models.Max("identificatie"))[
            "identificatie__max"
        ]
        number = int(max_id.split("-")[-1]) + 1
    else:
        number = 1

    padded_number = str(number).zfill(10)
    return f"{prefix}-{padded_number}"


def get_help_text(model_string: str, field_name: str) -> str:
    ModelClass = apps.get_model(model_string, require_ready=False)
    field = ModelClass._meta.get_field(field_name)
    return field.help_text


def get_view_summary(view_cls):
    """Return the viewset's general summary.

    This will extract the paragraphs between the first line and the first
    operation description.

    Example docstring:

        Some operation description here that will not be included.

        This text will be included below the tag.

        This text will also be included.

        create:
        First operation in the docstring which will not be included.


    :param type view_cls: the view class to extra the docstring from.
    """
    try:
        summary = view_cls.__doc__.split("\n\n", 1)[1].split(":", 1)[0]
        if "\n\n" in summary:
            summary = summary.rsplit("\n\n", 1)[0].strip().replace("\r", "")
            return formatting.dedent(smart_str(summary))
    except (AttributeError, IndexError):
        pass

    return ""


def get_field_attribute(
    model_string: str, field_name: str, attr_name: str
) -> Optional[str]:
    ModelClass = apps.get_model(model_string, require_ready=False)
    field = ModelClass._meta.get_field(field_name)
    return getattr(field, attr_name, None)


def get_domain() -> str:
    """
    Derive the domain where the application is hosted.
    """
    getter = import_string(settings.COMMONGROUND_API_COMMON_GET_DOMAIN)
    return getter()


def get_site_domain() -> str:
    """
    Derive the domain where the application is hosted.

    You can provide an alternative implementation via the
    ``COMMONGROUND_API_COMMON_GET_DOMAIN`` setting, which takes a dotted path to a
    callable taking no arguments.
    """
    if not apps.is_installed("django.contrib.sites"):
        raise ImproperlyConfigured(
            "'django.contrib.sites' is not installed in INSTALLED_APPS"
        )

    from django.contrib.sites.models import Site

    site = Site.objects.get_current()
    return site.domain
