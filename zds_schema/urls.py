from django.urls import path

from .views import ErrorDetailView, ScopesView

app_name = 'zds_schema'

urlpatterns = [
    path('fouten/<exception_class>/', ErrorDetailView.as_view(), name='error-detail'),
    path('scopes/', ScopesView.as_view(), name='scopes'),
]
