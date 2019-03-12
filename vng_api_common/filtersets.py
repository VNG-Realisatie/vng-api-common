from copy import deepcopy

from django.core.validators import URLValidator
from django.db import models

from django_filters.rest_framework import filterset

from .fields import RSINField
from .filters import RSINFilter, URLModelChoiceFilter

FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS[models.ForeignKey]['filter_class'] = URLModelChoiceFilter
FILTER_FOR_DBFIELD_DEFAULTS[models.OneToOneField]['filter_class'] = URLModelChoiceFilter

# register custom field(s)
FILTER_FOR_DBFIELD_DEFAULTS[RSINField] = {'filter_class': RSINFilter}
FILTER_FOR_DBFIELD_DEFAULTS[models.URLField]['extra'] = lambda f: {'validators': [URLValidator()]}


class FilterSet(filterset.FilterSet):
    """
    Allow foreign key fields to be filtered on resource URL.
    """
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS
