import warnings

from django.db import models
from django.utils.translation import gettext_lazy as _

from .etags import calculate_etag


class ETagMixin(models.Model):
    """
    Automatically calculate the (new) ETag value on save.

    Note that the signal receivers in :mod:`vng_api_common.caching.signals` are
    responsible for (cached) _etag value invalidation.
    """

    _etag = models.CharField(
        _("etag value"),
        max_length=32,
        help_text=_("MD5 hash of the resource representation in its current version."),
        editable=False,
    )

    class Meta:
        abstract = True

    def calculate_etag_value(self) -> str:
        """
        Calculate and save the ETag value.
        """
        if not self.pk:
            warnings.warn(
                "You should not calculate ETags on unsaved objects", RuntimeWarning
            )
        self._etag = calculate_etag(self)
        self.save(update_fields=["_etag"])
        return self._etag
