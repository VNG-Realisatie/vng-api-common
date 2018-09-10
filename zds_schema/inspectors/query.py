from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from django_filters.filters import ChoiceFilter
from drf_yasg import openapi
from drf_yasg.inspectors.query import CoreAPICompatInspector

from ..filters import URLModelChoiceFilter
from ..utils import underscore_to_camel


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
                model_field = queryset.model._meta.get_field(parameter.name)

                if isinstance(filter_field, URLModelChoiceFilter):
                    parameter.description = _("URL to the related resource")
                    parameter.format = openapi.FORMAT_URI
                elif isinstance(filter_field, ChoiceFilter):
                    parameter.enum = [choice[0] for choice in filter_field.extra['choices']]
                elif isinstance(model_field, models.URLField):
                    parameter.format = openapi.FORMAT_URI

                help_text = filter_field.extra.get('help_text', model_field.help_text)
                if not parameter.description and help_text:
                    parameter.description = force_text(model_field.help_text)

        return fields

    def process_result(self, result, method_name, obj, **kwargs):
        """
        Convert snake-case to camelCase.
        """
        if result and type(result) is list:
            for parameter in result:
                parameter.name = underscore_to_camel(parameter.name)
        return result
