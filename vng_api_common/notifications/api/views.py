from django.conf import settings
from django.utils.module_loading import import_string

from drf_yasg.utils import swagger_auto_schema
from notifications_api_common.api.serializers import NotificatieSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...permissions import AuthScopesRequired
from ...scopes import Scope
from ...serializers import FoutSerializer, ValidatieFoutSerializer
from ..constants import SCOPE_NOTIFICATIES_PUBLICEREN_LABEL


class NotificationBaseView(APIView):
    """
    Abstract view to receive webhooks
    """

    swagger_schema = None

    permission_classes = (AuthScopesRequired,)
    required_scopes = Scope(
        SCOPE_NOTIFICATIES_PUBLICEREN_LABEL
    )  # FIXME: this should be standalone!

    def get_serializer(self, *args, **kwargs):
        return NotificatieSerializer(*args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: "",
            400: ValidatieFoutSerializer,
            401: FoutSerializer,
            403: FoutSerializer,
            429: FoutSerializer,
            500: FoutSerializer,
            502: FoutSerializer,
            503: FoutSerializer,
        },
        operation_id="notification_receive",
        tags=["Notificaties"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.handle_notification(serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_notification(self, message):
        raise NotImplementedError("You must implemented `handle_notification`")


class NotificationView(NotificationBaseView):
    action = "create"
    permission_classes = (AuthScopesRequired,)
    required_scopes = {"create": Scope(SCOPE_NOTIFICATIES_PUBLICEREN_LABEL)}

    def create(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def handle_notification(self, message: dict) -> None:
        _handler = getattr(
            settings,
            "DEFAULT_NOTIFICATIONS_HANDLER",
            "vng_api_common.notifications.handlers.default",
        )
        handler = import_string(_handler)
        handler.handle(message)
