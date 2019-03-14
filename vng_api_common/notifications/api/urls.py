from django.urls import path

from .views import NotificationView

urlpatterns = [
    path('callbacks', NotificationView.as_view(), name='notificaties-webhook'),
]
