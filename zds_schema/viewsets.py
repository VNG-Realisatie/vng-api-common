from .utils import lookup_kwargs_to_filters


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
