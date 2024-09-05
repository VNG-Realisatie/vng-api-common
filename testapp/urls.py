from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularYAMLAPIView,
)
from rest_framework import routers

from vng_api_common.views import ViewConfigView
from vng_api_common.notifications.api.views import NotificationView

from .schema import custom_settings
from .viewsets import GroupViewSet, HobbyViewSet, PaginateHobbyViewSet, PersonViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("persons", PersonViewSet)
router.register("hobbies", HobbyViewSet)
router.register("groups", GroupViewSet)
router.register("paginate-hobbies", PaginateHobbyViewSet, basename="paginate-hobby")

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                # API documentation
                path(
                    "schema/openapi.json",
                    SpectacularJSONAPIView.as_view(
                        custom_settings=custom_settings,
                    ),
                    name="schema-json",
                ),
                path(
                    "schema/openapi.yaml",
                    SpectacularYAMLAPIView.as_view(
                        custom_settings=custom_settings,
                    ),
                    name="schema-yaml",
                ),
                path(
                    "schema/",
                    SpectacularRedocView.as_view(url_name="schema-yaml"),
                    name="schema-redoc",
                ),
            ]
            + router.urls
        ),
    ),
    path("api/", include(router.urls)),
    path("api/", include("vng_api_common.api.urls")),
    path("ref/", include("vng_api_common.urls")),
    path("view-config/", ViewConfigView.as_view(), name="view-config"),
    # this is a hack to get the parameter to show up in the API spec
    # this effectively makes this a wildcard URL, so it should be LAST
    path("<webhooks_path>", NotificationView.as_view()),
    path("", RedirectView.as_view(url="/api/")),
]
