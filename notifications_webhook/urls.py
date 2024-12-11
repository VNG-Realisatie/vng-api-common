from django.urls import path

from .views import NotificationView

urlpatterns = [
    path("<path:webhooks_path>", NotificationView.as_view()),
]
