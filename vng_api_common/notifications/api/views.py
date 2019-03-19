from django.conf import settings
from django.utils.module_loading import import_string

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...permissions import ScopesRequired
from ...scopes import Scope
from ..constants import SCOPE_NOTIFICATIES_PUBLICEREN_LABEL
from .serializers import NotificatieSerializer


class NotificationBaseView(APIView):
    """
    Abstract view to receive webhooks
    """
    swagger_schema = None

    permission_classes = (ScopesRequired,)
    required_scopes = Scope(SCOPE_NOTIFICATIES_PUBLICEREN_LABEL)

    def post(self, request, *args, **kwargs):
        serializer = NotificatieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.handle_notification(serializer.validated_data)
        return Response(status=status.HTTP_200_OK)

    def handle_notification(self, message):
        raise NotImplementedError("You must implemented `handle_notification`")


class NotificationView(NotificationBaseView):
    def handle_notification(self, message: dict) -> None:
        _handler = getattr(
            settings, 'DEFAULT_NOTIFICATIONS_HANDLER',
            'vng_api_common.notifications.handlers.default'
        )
        handler = import_string(_handler)
        handler.handle(message)
