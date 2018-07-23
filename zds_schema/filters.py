from django_filters.rest_framework import DjangoFilterBackend

from .search import is_search_view


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
