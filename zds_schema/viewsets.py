class NestedViewSetMixin:
    def get_queryset(self):
        """
        Filter the ``QuerySet`` based on its parents.
        """
        queryset = super().get_queryset()
        serializer_class = self.get_serializer_class()

        lookup_kwargs = getattr(serializer_class, 'parent_lookup_kwargs', {})
        filters = {}
        for kwarg, field_name in lookup_kwargs.items():
            if kwarg not in self.kwargs:
                continue
            filters[field_name] = self.kwargs[kwarg]

        return queryset.filter(**filters)
