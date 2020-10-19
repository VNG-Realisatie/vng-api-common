from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from rest_framework import routers

from .schema import SchemaView
from .views import NotificationView
from .viewsets import GroupViewSet

router = routers.DefaultRouter()
router.register("groups", GroupViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                # API documentation
                re_path(
                    r"^schema/openapi(?P<format>\.json|\.yaml)$",
                    SchemaView.without_ui(cache_timeout=None),
                    name="schema-json",
                ),
                re_path(
                    r"^schema/$",
                    SchemaView.with_ui("redoc", cache_timeout=None),
                    name="schema-redoc",
                ),
            ]
            + router.urls
        ),
    ),
    path("api/", include("vng_api_common.api.urls")),
    path("ref/", include("vng_api_common.urls")),
    # this is a hack to get the parameter to show up in the API spec
    # this effectively makes this a wildcard URL, so it should be LAST
    path("<webhooks_path>", NotificationView.as_view()),
    path("", RedirectView.as_view(url="/api/")),
]
