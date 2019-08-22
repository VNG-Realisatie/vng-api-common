from django.urls import include, path

urlpatterns = [
    path("api/", include("vng_api_common.notifications.api.urls")),
    path("api/", include("notifications.api.urls")),
    path("_dummy", include("vng_api_common.urls")),
]
