from django.db import models

from rest_framework.response import Response


def is_search_view(view):
    _action = getattr(view, "action", None)
    if _action is None:
        return
    action = getattr(view, view.action, None)
    return getattr(action, "is_search_action", False)


class SearchMixin:
    search_input_serializer_class = None

    def get_search_input_serializer_class(self):
        return self.search_input_serializer_class or self.serializer_class

    def get_search_input(self):
        serializer = self.get_search_input_serializer_class()(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def get_search_output(self, queryset: models.QuerySet):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
