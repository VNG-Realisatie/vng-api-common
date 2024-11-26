from vng_api_common.notifications.api.views import NotificationView as _NotificationView
from vng_api_common.schema import AutoSchema


class NotificationView(_NotificationView):
    """
    Ontvang notificaties via webhook
    """
    schema = AutoSchema()
