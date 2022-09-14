from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import SpectacularRedocView, SpectacularYAMLAPIView
from rest_framework import routers

from .views import NotificationView
from .viewsets import GroupViewSet, HobbyViewSet, PersonViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("persons", PersonViewSet)
router.register("hobbies", HobbyViewSet)
router.register("groups", GroupViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                # API documentation
                path(
                    "schema/openapi.yaml",
                    SpectacularYAMLAPIView.as_view(),
                    name="schema-json",
                ),
                path(
                    "schema/",
                    SpectacularRedocView.as_view(),
                    name="schema-redoc",
                ),
            ]
            + router.urls
        ),
    ),
    path("api/", include(router.urls)),
    path("api/", include("vng_api_common.api.urls")),
    path("ref/", include("vng_api_common.urls")),
    # this is a hack to get the parameter to show up in the API spec
    # this effectively makes this a wildcard URL, so it should be LAST
    path("<webhooks_path>", NotificationView.as_view()),
    path("", RedirectView.as_view(url="/api/")),
]
