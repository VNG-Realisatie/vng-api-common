from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings
from rest_framework_nested.viewsets import NestedViewSetMixin  # noqa

from .filters import Backend
from .utils import underscore_to_camel


class CheckQueryParamsMixin:
    def _check_query_params(self, request) -> None:
        """
        Validate that the query params in the request are known.
        """
        # nothing to check if there are no query parameters
        if not request.query_params:
            return

        # NOTE: only works with django_filters based filter backends
        backend = Backend()
        queryset = self.get_queryset()
        filterset_class = backend.get_filterset_class(self, queryset)

        known_params = set()
        if filterset_class:
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
                raise NotImplementedError(
                    "Unknown paginator class: %s" % type(self.paginator)
                )

        unknown_params = set(request.query_params.keys()) - known_params
        if OrderingFilter in self.filter_backends:
            unknown_params.discard(api_settings.ORDERING_PARAM)

        if unknown_params:
            msg = _("Onbekende query parameters: %s" % ", ".join(unknown_params))
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: msg}, code="unknown-parameters"
            )

    def list(self, request, *args, **kwargs):
        self._check_query_params(request)
        return super().list(request, *args, **kwargs)
