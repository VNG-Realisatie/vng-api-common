from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings

from .filters import Backend
from .utils import lookup_kwargs_to_filters, underscore_to_camel


class NestedViewSetMixin:
    def get_queryset(self):
        """
        Filter the ``QuerySet`` based on its parents.
        """
        queryset = super().get_queryset()
        serializer_class = self.get_serializer_class()

        lookup_kwargs = getattr(serializer_class, 'parent_lookup_kwargs', {})
        filters = lookup_kwargs_to_filters(lookup_kwargs, self.kwargs)

        return queryset.filter(**filters)


class CheckQueryParamsMixin:

    def _check_query_params(self, request) -> None:
        """
        Validate that the query params in the request are known.
        """
        # nothing to check if there are no query parameters
        if not request.query_params:
            return

        # TODO: check for pagination params
        # NOTE: only works with django_filters based filter backends
        backend = Backend()
        queryset = self.get_queryset()
        filterset_class = backend.get_filterset_class(self, queryset)

        # build a list of known params from the filters
        filters = filterset_class().get_filters().keys()

        known_params = {underscore_to_camel(param) for param in filters}

        # add the pagination params to the known params
        if self.paginator:
            if isinstance(self.paginator, PageNumberPagination):
                known_params.add(self.paginator.page_query_param)
                if self.paginator.page_size_query_param:
                    known_params.add(self.paginator.page_size_query_param)
            else:
                raise NotImplementedError("Unknown paginator class: %s" % type(self.paginator))

        unknown_params = set(request.query_params.keys()) - known_params
        if unknown_params:
            msg = _("Onbekende query parameters: %s" % ", ".join(unknown_params))
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: msg},
                code='unknown-parameters'
            )

    def list(self, request, *args, **kwargs):
        self._check_query_params(request)
        return super().list(request, *args, **kwargs)
