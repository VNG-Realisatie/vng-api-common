from typing import Optional, Type

from django.db import models
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from rest_framework import serializers
from rest_framework.status import HTTP_200_OK
from rest_framework.utils.model_meta import get_field_info
from rest_framework.views import APIView

CACHE_REQUEST_HEADERS = [
    OpenApiParameter(
        name="If-None-Match",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
        required=False,
        description=_(
            "Perform conditional requests. This header should contain one or "
            "multiple ETag values of resources the client has cached. If the "
            "current resource ETag value is in this set, then an HTTP 304 "
            "empty body will be returned. See "
            "[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match) "
            "for details."
        ),
        examples=[
            OpenApiExample(
                "oneValue",
                summary=_("One ETag value"),
                value='"79054025255fb1a26e4bc422aef54eb4"',
            ),
            OpenApiExample(
                "multipleValues",
                summary=_("Multiple ETag values"),
                value='"79054025255fb1a26e4bc422aef54eb4", "e4d909c290d0fb1ca068ffaddf22cbd0"',
            ),
        ],
    )
]


def get_target_field(model: Type[models.Model], field: str) -> Optional[models.Field]:
    """
    Retrieve the end-target that ``field`` points to.

    :param field: A string containing a lookup, potentially spanning relations. E.g.:
      foo__bar__lte.
    :return: A Django model field instance or `None`
    """

    start, *remaining = field.split("__")
    field_info = get_field_info(model)

    # simple, non relational field?
    if start in field_info.fields:
        return field_info.fields[start]

    # simple relational field?
    if start in field_info.forward_relations:
        relation_info = field_info.forward_relations[start]
        if not remaining:
            return relation_info.model_field
        else:
            return get_target_field(relation_info.related_model, "__".join(remaining))

    # check the reverse relations - note that the model name is used instead of model_name_set
    # in the queries -> we can't just test for containment in field_info.reverse_relations
    for relation_info in field_info.reverse_relations.values():
        # not sure about this - what if there are more relations with different related names?
        if relation_info.related_model._meta.model_name != start:
            continue
        return get_target_field(relation_info.related_model, "__".join(remaining))

    return None


def has_geo_fields(serializer) -> bool:
    """
    Check if any of the serializer fields are a GeometryField.
    If the serializer has nested serializers, a depth-first search is done
    to check if the nested serializers has `GeometryField`\ s.
    """
    try:
        from rest_framework_gis.fields import GeometryField
    except ImportError:
        return False

    for field in serializer.fields.values():
        if isinstance(field, serializers.Serializer):
            has_nested_geo_fields = has_geo_fields(field)
            if has_nested_geo_fields:
                return True

        elif isinstance(field, (serializers.ListSerializer, serializers.ListField)):
            field = field.child

        if isinstance(field, GeometryField):
            return True

    return False


def get_cache_headers(view: APIView) -> [OpenApiParameter]:
    # import here due to extensions loading in a early stage
    from ..caching.introspection import has_cache_header

    if not has_cache_header(view):
        return []

    return [
        OpenApiParameter(
            name="ETag",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description=_(
                "De ETag berekend op de response body JSON. "
                "Indien twee resources exact dezelfde ETag hebben, dan zijn "
                "deze resources identiek aan elkaar. Je kan de ETag gebruiken "
                "om caching te implementeren."
            ),
            response=[HTTP_200_OK],
        ),
    ]
