from vng_api_common.conf.api import BASE_SWAGGER_SETTINGS
from vng_api_common.notifications.api.views import NotificationView as _NotificationView


class NotificationView(_NotificationView):
    """
    Ontvang notificaties via webhook
    """

    swagger_schema = BASE_SWAGGER_SETTINGS["DEFAULT_AUTO_SCHEMA_CLASS"]
