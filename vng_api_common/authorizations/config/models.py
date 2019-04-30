from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.constants import ComponentTypes
from vng_api_common.models import ClientConfig


class AuthorizationsConfig(ClientConfig):
    component = models.CharField(
        _("component"), max_length=50, default=ComponentTypes.zrc,
        choices=ComponentTypes.choices
    )

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")

    def __init__(self, *args, **kwargs):
        # set api_root default value
        api_root_field = self._meta.get_field('api_root')
        api_root_field.default = 'https://ref.tst.vng.cloud/ac/api/v1'

        super().__init__(*args, **kwargs)
