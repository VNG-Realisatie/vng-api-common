from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('vng_api_common.notifications.api.urls')),
]
