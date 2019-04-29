from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.constants import ComponentTypes
from vng_api_common.models import ClientConfig


class AuthorizationsConfig(ClientConfig):
    component = models.CharField(_("component"), max_length=50, choices=ComponentTypes.choices)

    class Meta:
        verbose_name = _("Autorisatiecomponentconfiguratie")
