import logging

from djangorestframework_camel_case.util import underscoreize

from ..authorizations.models import Applicatie
from ..authorizations.serializers import ApplicatieUuidSerializer
from ..client import get_client
from ..constants import CommonResourceAction
from ..utils import get_uuid_from_path


class LoggingHandler:
    def handle(self, message: dict) -> None:
        logger = logging.getLogger("notifications")
        logger.info("Received notification %r", message)


class AuthHandler:
    def _request_auth(self, url: str) -> dict:
        client = get_client(url)
        response = client.retrieve("applicatie", url)
        return underscoreize(response)

    def handle(self, message: dict) -> None:
        uuid = get_uuid_from_path(message["resource_url"])

        if message["actie"] == CommonResourceAction.destroy:
            Applicatie.objects.filter(uuid=uuid).delete()
            return

        # get info
        applicatie_data = self._request_auth(message["resource_url"])
        applicatie_data["uuid"] = uuid

        # update models
        try:
            applicatie = Applicatie.objects.get(uuid=uuid)
        except Applicatie.DoesNotExist:
            applicatie_serializer = ApplicatieUuidSerializer(data=applicatie_data)
        else:
            applicatie_serializer = ApplicatieUuidSerializer(
                applicatie, data=applicatie_data
            )
        applicatie_serializer.is_valid()
        applicatie_serializer.save()


class RoutingHandler:
    def __init__(self, config: dict, default=None):
        self.config = config
        self.default = default

    def handle(self, message: dict):
        handler = self.config.get(message["kanaal"])
        if handler is not None:
            handler.handle(message)
        elif self.default:
            self.default.handle(message)


log = LoggingHandler()
auth = AuthHandler()

default = RoutingHandler({"autorisaties": auth}, default=log)
