import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from vng_api_common.constants import SCOPE_NOTIFICATIES_PUBLICEREN_LABEL
from vng_api_common.models import APICredential
from vng_api_common.notifications.models import NotificationsConfig

logger = logging.getLogger(__name__)


class KanaalExists(Exception):
    pass


def create_kanaal(api_root: str, kanaal: str) -> None:
    """
    Create a kanaal, if it doesn't exist yet.
    """
    Client = import_string(settings.ZDS_CLIENT_CLASS)

    if not api_root.endswith('/'):
        api_root = f"{api_root}/"

    client = Client.from_url(api_root)
    client.base_url = api_root
    client.auth = APICredential.get_auth(
        api_root,
        scopes=[SCOPE_NOTIFICATIES_PUBLICEREN_LABEL]
    )

    # kanalen = client.list('kanaal', query_params={'naam': kanaal})
    kanalen = [x for x in client.list('kanaal') if x['naam'] == kanaal]
    if kanalen:
        raise KanaalExists()

    client.create('kanaal', {'naam': kanaal})


class Command(BaseCommand):
    help = 'Create kanaal in notification component'

    def add_arguments(self, parser):
        parser.add_argument('kanaal', nargs='?', type=str, help='Name of kanaal')
        parser.add_argument(
            '--nc-api-root',
            help="API root of the NC, default value taken from notifications config"
        )

    def handle(self, **options):
        config = NotificationsConfig.get_solo()

        # use CLI arg or fall back to database config
        api_root = options['nc_api_root'] or config.api_root

        # use CLI arg or fall back to setting
        kanaal = options['kanaal'] or settings.NOTIFICATIES_KANAAL

        try:
            create_kanaal(api_root, kanaal)
            self.stdout.write(f"Registered kanaal '{kanaal}' with {api_root}")
        except KanaalExists:
            self.stderr.write(f"Kanaal '{kanaal}' already exists within {api_root}")
