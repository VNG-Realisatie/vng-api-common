from django.db import models
from django.utils.translation import ugettext_lazy as _

from .etags import calculate_etag


class ETagMixin(models.Model):
    """
    Automatically calculate the (new) ETag value on save.
    """

    _etag = models.CharField(
        _("etag value"),
        max_length=32,
        help_text=_("MD5 hash of the resource representation in its current version."),
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # TODO: change into post-save to handle pk?
        self._etag = calculate_etag(self)
        super().save(*args, **kwargs)
