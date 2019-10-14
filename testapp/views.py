from drf_yasg.app_settings import swagger_settings

from vng_api_common.notifications.api.views import NotificationView as _NotificationView


class NotificationView(_NotificationView):
    """
    Ontvang notificaties via webhook
    """

    swagger_schema = swagger_settings.DEFAULT_AUTO_SCHEMA_CLASS
