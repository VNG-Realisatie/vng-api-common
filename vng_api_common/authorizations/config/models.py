from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from solo.models import SingletonModel
from zds_client import Client


class AuthorizationsConfig(SingletonModel):
    api_root = models.URLField(_("api root"), unique=True, default='https://ref.tst.vng.cloud/ac/api/v1')
    component = models.CharField(_("component"), max_length=50, default='ZRC')

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")

    def __str__(self):
        return self.api_root

    @classmethod
    def get_client(cls) -> Client:
        """
        Construct a client, prepared with the required auth.
        """
        config = cls.get_solo()
        Client = import_string(settings.ZDS_CLIENT_CLASS)

        api_root = config.api_root
        if not api_root:
            raise ImproperlyConfigured(f"Configure the AC API root in '{cls._meta.verbose_name}'")

        if not api_root.endswith('/'):
            api_root = f"{api_root}/"

        client = Client.from_url(api_root)
        client.base_url = api_root

        return client
