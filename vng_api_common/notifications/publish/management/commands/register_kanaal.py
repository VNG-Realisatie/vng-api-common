import json
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string
from django.core.serializers.json import DjangoJSONEncoder

from vng_api_common.constants import SCOPE_NOTIFICATIES_PUBLICEREN_LABEL
from vng_api_common.models import APICredential


logger = logging.getLogger(__name__)


def request_create_kanaal(kanaal_name):
    Client = import_string(settings.ZDS_CLIENT_CLASS)
    url = settings.NOTIFICATIES_KANAAL_URL
    client = Client.from_url(url)
    client.auth = APICredential.get_auth(
        url,
        scopes=[SCOPE_NOTIFICATIES_PUBLICEREN_LABEL]
    )
    msg = {"naam": kanaal_name}

    response = client.request(
        url, 'kanaal',
        method='POST',
        data=json.dumps(msg, cls=DjangoJSONEncoder),
        expected_status=201
    )


class Command(BaseCommand):
    help = 'Create kanaal in notification component'

    def add_arguments(self, parser):
        parser.add_argument('kanaal', nargs='?', type=str, help='Name of kanaal')

    def handle(self, *args, **kwargs):
        kanaal = kwargs.get('kanaal', None)
        if kanaal is None:
            kanaal = settings.NOTIFICATIES_KANAAL
        request_create_kanaal(kanaal)
