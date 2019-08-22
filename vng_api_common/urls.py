from django.urls import path

from .views import ErrorDetailView, ScopesView

app_name = "vng_api_common"

urlpatterns = [
    path("fouten/<exception_class>/", ErrorDetailView.as_view(), name="error-detail"),
    path("scopes/", ScopesView.as_view(), name="scopes"),
]
