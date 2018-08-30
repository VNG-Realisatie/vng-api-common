from django.urls import path

from .views import ErrorDetailView

app_name = 'zds_schema'

urlpatterns = [
    path('fouten/<exception_class>/', ErrorDetailView.as_view(), name='error-detail'),
]
