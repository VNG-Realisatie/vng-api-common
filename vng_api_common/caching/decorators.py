from functools import partial
from typing import Optional, Set

from rest_framework_condition.decorators import condition as drf_condition

from .etags import etag_func
from .registry import extract_dependencies


def conditional_retrieve(
    action="retrieve",
    etag_field="_etag",
    extra_depends_on: Optional[Set[str]] = None,
):
    """
    Decorate a viewset to apply conditional GET requests.

    The decorator patches the handler to calculate and emit the required ETag-related
    headers. Additionally, it sets up the dependency tree for the exposed resource so
    that the ETag value can be recalculated when the resource or relevant related
    resources are modified, resulting in an updated ETag value. This is introspected
    through the specified viewset serializer class.

    :param action: The viewset action to decorate
    :param etag_field: The model field containing the (cached) ETag value
    :param extra_depends_on: A set of additional field names the ETag value calculation
      depends on. Normally, this is inferred from the serializer, but in some cases (
      .e.g. ``SerializerMethodField``) this cannot be automatically detected. These
      fields will be added to the automatically introspected serializer relations.
    """

    def decorator(viewset: type):
        extract_dependencies(viewset, extra_depends_on or set())
        condition = drf_condition(etag_func=partial(etag_func, etag_field=etag_field))
        original_handler = getattr(viewset, action)
        handler = condition(original_handler)
        setattr(viewset, action, handler)
        if not hasattr(viewset, "_conditional_retrieves"):
            viewset._conditional_retrieves = []
        viewset._conditional_retrieves.append(action)
        return viewset

    return decorator
