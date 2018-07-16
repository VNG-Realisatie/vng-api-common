from django.core import checks
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .constants import RSIN_LENGTH
from .validators import validate_rsin


class RSINField(models.CharField):
    default_validators = [validate_rsin]
    description = _("RSIN")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', RSIN_LENGTH)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_fixed_max_length_attribute(**kwargs))
        return errors

    def _check_fixed_max_length_attribute(self, **kwargs):
        if self.max_length != RSIN_LENGTH:
            return [
                checks.Error(
                    "RSINField may not override 'max_length' attribute.",
                    obj=self,
                    id='zds_schema.fields.E001',
                )
            ]
        return []
