from rest_framework.pagination import PageNumberPagination


class DynamicPageSizeMixin:
    page_size = 100
    page_size_query_param = "pageSize"
    max_page_size = 500


class DynamicPageSizePagination(DynamicPageSizeMixin, PageNumberPagination): ...
