from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db.models import ObjectDoesNotExist
from django.forms.widgets import URLInput
from django.utils.translation import ugettext_lazy as _

from django_filters import fields, filters
from django_filters.rest_framework import DjangoFilterBackend

from .search import is_search_view
from .utils import get_resource_for_path


class Backend(DjangoFilterBackend):

    def filter_queryset(self, request, queryset, view):
        """
        Also filter on request.data if request.query_params is empty
        """
        if not is_search_view(view):
            return super().filter_queryset(request, queryset, view)

        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            return filter_class(request.data, queryset=queryset, request=request).qs

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
            except ObjectDoesNotExist:
                raise ValidationError(_("Invalid resource URL supplied"), code='invalid')
        return super().to_python(value)


class URLModelChoiceFilter(filters.ModelChoiceFilter):
    field_class = URLModelChoiceField
