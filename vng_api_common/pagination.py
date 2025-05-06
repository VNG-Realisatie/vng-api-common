from django.utils.translation import gettext_lazy as _

from rest_framework.pagination import PageNumberPagination

# These strings are defined by rest_framework.pagination, but never translated
FORCE_TRANSLATION_STRINGS = [
    _("A page number within the paginated result set."),
    _("Number of results to return per page."),
]


class DynamicPageSizeMixin:
    page_size = 100
    page_size_query_param = "pageSize"
    max_page_size = 500
    page_size_query_description = _("Het aantal resultaten terug te geven per pagina. (default: 100).")


class DynamicPageSizePagination(DynamicPageSizeMixin, PageNumberPagination): ...
