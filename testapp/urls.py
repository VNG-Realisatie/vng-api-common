from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularYAMLAPIView,
)

from vng_api_common import routers
from vng_api_common.views import ViewConfigView

from .viewsets import GroupViewSet, HobbyViewSet, PaginateHobbyViewSet, PersonViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("persons", PersonViewSet)
router.register("hobbies", HobbyViewSet)
router.register(
    "groups",
    GroupViewSet,
    [routers.nested("nested-person", PersonViewSet, basename="nested-person")],
)
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
                    SpectacularJSONAPIView.as_view(),
                    name="schema-json",
                ),
                path(
                    "schema/openapi.yaml",
                    SpectacularYAMLAPIView.as_view(),
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
    path("", RedirectView.as_view(url="/api/")),
]
