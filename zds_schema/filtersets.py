from copy import deepcopy

from django.db import models

from django_filters.rest_framework import filterset

from .filters import URLModelChoiceFilter

FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS[models.ForeignKey]['filter_class'] = URLModelChoiceFilter


class FilterSet(filterset.FilterSet):
    """
    Allow foreign key fields to be filtered on resource URL.
    """
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS
