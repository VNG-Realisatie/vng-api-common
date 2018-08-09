from django.db import models
from django.utils.translation import ugettext as _

from django_filters.filters import ChoiceFilter
from drf_yasg import openapi
from drf_yasg.inspectors.query import CoreAPICompatInspector

from ..filters import URLModelChoiceFilter


class FilterInspector(CoreAPICompatInspector):
    """
    Filter inspector that specifies the format of URL-based fields and lists
    enum options.
    """

    def get_filter_parameters(self, filter_backend):
        fields = super().get_filter_parameters(filter_backend)
        if fields:
            queryset = self.view.get_queryset()
            filter_class = filter_backend.get_filter_class(self.view, queryset)

            for parameter in fields:
                filter_field = filter_class.base_filters[parameter.name]

                if isinstance(filter_field, URLModelChoiceFilter):
                    parameter.description = _("URL to the related resource")
                    parameter.format = openapi.FORMAT_URI
                elif isinstance(filter_field, ChoiceFilter):
                    parameter.enum = [choice[0] for choice in filter_field.extra['choices']]
                else:
                    model_field = queryset.model._meta.get_field(parameter.name)
                    if isinstance(model_field, models.URLField):
                        parameter.format = openapi.FORMAT_URI

        return fields
