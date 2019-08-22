from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

info = openapi.Info(
    title="Notifications webhook receiver",
    default_version="v1",
    description="API Specification to be able to receive notifications from the NRC",
    contact=openapi.Contact(url="https://github.com/VNG-Realisatie/gemma-zaken"),
)


SchemaView = get_schema_view(public=True, permission_classes=(permissions.AllowAny,))
