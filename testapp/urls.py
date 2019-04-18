from django.contrib import admin
from django.urls import include, path, re_path

from .schema import SchemaView
from .views import NotificationView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include([
        # API documentation
        re_path(r'^schema/openapi(?P<format>\.json|\.yaml)$',
                SchemaView.without_ui(cache_timeout=None),
                name='schema-json'),
        re_path(r'^schema/$',
                SchemaView.with_ui('redoc', cache_timeout=None),
                name='schema-redoc'),

        path('webhooks', NotificationView.as_view()),
    ])),
]
