from copy import deepcopy

from django.core.validators import URLValidator
from django.db import models

from django_filters.rest_framework import filterset

from .fields import RSINField
from .filters import RSINFilter, URLModelChoiceFilter

FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS[models.ForeignKey]["filter_class"] = URLModelChoiceFilter
FILTER_FOR_DBFIELD_DEFAULTS[models.OneToOneField]["filter_class"] = URLModelChoiceFilter

# register custom field(s)
FILTER_FOR_DBFIELD_DEFAULTS[RSINField] = {"filter_class": RSINFilter}
FILTER_FOR_DBFIELD_DEFAULTS[models.URLField]["extra"] = lambda f: {
    "validators": [URLValidator()]
}


class FilterSet(filterset.FilterSet):
    """
    Allow foreign key fields to be filtered on resource URL.
    """

    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    @classmethod
    def filter_for_field(cls, field, field_name, lookup_expr=None):
        """
        Add help texts for model field filters
        """
        filter_set = super().filter_for_field(field, field_name, lookup_expr)
        if not filter_set.extra.get("help_text"):
            filter_set.extra["help_text"] = getattr(field, "help_text", None)
        return filter_set
