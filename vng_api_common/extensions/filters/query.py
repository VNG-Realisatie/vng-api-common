from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import gettext as _

from django_filters.filters import BaseCSVFilter, ChoiceFilter
from drf_spectacular.extensions import OpenApiFilterExtension
from rest_framework.filters import OrderingFilter

from vng_api_common.extensions.utils import get_target_field
from vng_api_common.filters import URLModelChoiceFilter
from vng_api_common.oas import TYPE_ARRAY, TYPE_STRING
from vng_api_common.utils import underscore_to_camel


class FilterExtension(OpenApiFilterExtension):
    target_class = "vng_api_common.filters.Backend"
    match_subclasses = True

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        default_parameters = self.target.get_schema_operation_parameters(
            auto_schema.view
        )
        filterset_class = getattr(auto_schema.view, "filterset_class", None)

        if isinstance(self.target, OrderingFilter) or not filterset_class:
            # TODO: OrderingFilter not present in ZRC, test in other components
            return default_parameters

        queryset = auto_schema.view.get_queryset()

        for parameter in default_parameters:
            filter_field = filterset_class.base_filters[parameter["name"]]
            model_field = get_target_field(queryset.model, parameter["name"])

            parameter_name = underscore_to_camel(parameter["name"])

            original_description = parameter.get("description")
            help_text = filter_field.extra.get(
                "help_text",
                getattr(model_field, "help_text", "") if model_field else "",
            )

            if isinstance(filter_field, BaseCSVFilter):
                schema = {
                    "type": TYPE_ARRAY,
                    "items": {
                        "type": TYPE_STRING,
                    },
                }

                if "choices" in filter_field.extra:
                    schema["items"]["enum"] = (
                        [choice[0] for choice in filter_field.extra["choices"]],
                    )

                parameter["schema"] = schema
                parameter["style"] = "form"
                parameter["explode"] = False
            elif isinstance(filter_field, URLModelChoiceFilter):
                description = _("URL to the related {resource}").format(
                    resource=parameter_name
                )
                parameter["description"] = help_text or description
                parameter["schema"]["format"] = "uri"
            elif isinstance(filter_field, ChoiceFilter):
                parameter["schema"]["enum"] = [
                    choice[0] for choice in filter_field.extra["choices"]
                ]
            elif model_field and isinstance(model_field, models.URLField):
                parameter["schema"]["format"] = "uri"

            if parameter["description"] == original_description and help_text:
                parameter["description"] = force_text(help_text)

            if "max_length" in filter_field.extra:
                parameter["schema"]["maxLength"] = filter_field.extra["max_length"]
            if "min_length" in filter_field.extra:
                parameter["schema"]["minLength"] = filter_field.extra["min_length"]

            parameter["name"] = parameter_name

        return default_parameters
