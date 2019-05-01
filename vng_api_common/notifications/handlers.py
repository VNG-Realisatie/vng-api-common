import logging

from django.conf import settings
from django.utils.module_loading import import_string

from djangorestframework_camel_case.util import underscoreize

from vng_api_common.authorizations.models import Applicatie
from vng_api_common.authorizations.serializers import ApplicatieUuidSerializer
from vng_api_common.utils import get_identifier_from_path


class LoggingHandler:

    def handle(self, message: dict) -> None:
        logger = logging.getLogger('notifications')
        logger.info("Received notification %r", message)


class AuthHandler:
    def handle_auth(self, message: dict) -> None:

        # uuids in AC DB are synchronized with uuids in local DB
        uuid = get_identifier_from_path(message['resource_url'])
        
        if message['actie'] == 'delete':
            Applicatie.objects.get(uuid=uuid).delete()
            return

        # get info
        applicatie_data = self._request_auth(message['resource_url'])
        applicatie_data['uuid'] = uuid

        # update models
        try:
            applicatie = Applicatie.objects.get(uuid=uuid)
        except Applicatie.DoesNotExist:
            applicatie_serializer = ApplicatieUuidSerializer(data=applicatie_data)
        else:
            applicatie_serializer = ApplicatieUuidSerializer(applicatie, data=applicatie_data)
        applicatie_serializer.is_valid()
        applicatie_serializer.save()
        
    def _request_auth(self, path: str) -> dict:
        Client = import_string(settings.ZDS_CLIENT_CLASS)
        client = Client.from_url(path)
        response = client.retrieve('applicatie', path)
        return underscoreize(response)

    def handle(self, message: dict) -> None:
        if message['kanaal'] == 'autorisaties':
            self.handle_auth(message)

        else:
            logger = logging.getLogger('notifications')
            logger.info("Received notification %r", message)


default = LoggingHandler()
auth_handler = AuthHandler()
