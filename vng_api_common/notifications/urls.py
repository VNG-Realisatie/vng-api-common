from django.urls import path

from .views import KanalenView

app_name = "notifications"

urlpatterns = [path("kanalen/", KanalenView.as_view(), name="kanalen")]
