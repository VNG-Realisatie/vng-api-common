from urllib.parse import urlencode, urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.forms.widgets import URLInput
from django.http import QueryDict
from django.utils.translation import ugettext_lazy as _

from django_filters import fields, filters
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from djangorestframework_camel_case.util import underscoreize

from .search import is_search_view
from .utils import get_resource_for_path


class Backend(DjangoFilterBackend):

    # Taken from drf_yasg.inspectors.field.CamelCaseJSONFilter
    def _is_camel_case(self, view):
        return (
            any(issubclass(parser, CamelCaseJSONParser) for parser in view.parser_classes) or
            any(issubclass(renderer, CamelCaseJSONRenderer) for renderer in view.renderer_classes)
        )

    def _transform_query_params(self, view, query_params: QueryDict) -> QueryDict:
        if not self._is_camel_case(view):
            return query_params

        # data can be a regular dict if it's coming from a serializer
        if hasattr(query_params, 'lists'):
            data = dict(query_params.lists())
        else:
            data = query_params

        transformed = underscoreize(data)

        return QueryDict(urlencode(transformed, doseq=True))

    def filter_queryset(self, request, queryset, view):
        """
        Filter the queryset.

        * filter on request.data if request.query_params is empty
        * do the camelCase transformation of filter parameters
        """
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            filter_parameters = request.query_params if not is_search_view(view) else request.data
            query_params = self._transform_query_params(view, filter_parameters)
            return filter_class(query_params, queryset=queryset, request=request).qs

        return queryset


class URLModelChoiceField(fields.ModelChoiceField):
    widget = URLInput

    def url_to_pk(self, url: str):
        parsed = urlparse(url)
        instance = get_resource_for_path(parsed.path)
        model = self.queryset.model
        if not isinstance(instance, model):
            raise ValidationError(_("Invalid resource type supplied, expected %r") % model, code='invalid-type')
        return instance.pk

    def to_python(self, value: str):
        # TODO: validate that it's proper URL input
        if value:
            try:
                value = self.url_to_pk(value)
            except models.ObjectDoesNotExist:
                raise ValidationError(_("Invalid resource URL supplied"), code='invalid')
        return super().to_python(value)


class URLModelChoiceFilter(filters.ModelChoiceFilter):
    field_class = URLModelChoiceField
