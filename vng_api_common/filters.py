import logging
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.forms.widgets import URLInput
from django.utils.translation import gettext_lazy as _

from django_filters import fields, filters
from django_filters.constants import EMPTY_VALUES

from .constants import FILTER_URL_DID_NOT_RESOLVE
from .utils import NotAViewSet, get_resource_for_path
from .validators import validate_rsin

logger = logging.getLogger(__name__)


class URLModelChoiceField(fields.ModelChoiceField):
    widget = URLInput

    def __init__(self, *args, **kwargs):
        self.instance_path = kwargs.pop("instance_path", None)
        super().__init__(*args, **kwargs)

    # Placeholder - gets replaced by URLModelChoiceFilter
    def _get_request(self):
        return None

    def url_to_pk(self, url: str):
        parsed = urlparse(url)
        path = parsed.path

        # this field only supports local FKs - so if we see a domain that does
        # not match the current host, this cannot possibly yield any results
        request = self._get_request()
        if request is not None:
            host = request.get_host()
            if parsed.netloc != host:
                raise NotAViewSet("External URL cannot map to a local viewset")

        instance = get_resource_for_path(path)
        if self.instance_path:
            for bit in self.instance_path.split("."):
                instance = getattr(instance, bit)
        model = self.queryset.model
        if not isinstance(instance, model):
            raise ValidationError(
                _("Invalid resource type supplied, expected %r") % model,
                code="invalid-type",
            )
        return instance.pk

    def to_python(self, value: str):
        if value is not None:
            URLValidator()(value)

        if value:
            try:
                value = self.url_to_pk(value)
            except NotAViewSet:
                logger.info("No %s found for URL %s", self.label, value)
                return FILTER_URL_DID_NOT_RESOLVE
            except models.ObjectDoesNotExist:
                logger.info("No %s found for URL %s", self.label, value)
                return FILTER_URL_DID_NOT_RESOLVE
        return super().to_python(value)


class URLModelChoiceFilter(filters.ModelChoiceFilter):
    field_class = URLModelChoiceField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_path = kwargs.get("instance_path", None)
        self.queryset = kwargs.get("queryset")

    @property
    def field(self):
        field = super().field
        # we need access to the request in the backing field...
        field._get_request = self.get_request
        return field

    def filter(self, qs, value):
        # If the URL did not resolve to an instance, return no results
        if value == FILTER_URL_DID_NOT_RESOLVE:
            return qs.none()
        return super().filter(qs, value)


class RSINFilter(filters.CharFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("validators", [validate_rsin])
        super().__init__(*args, **kwargs)


class WildcardFilter(filters.CharFilter):
    """
    Filters the queryset based on a string and optionally allows wildcards in
    the query parameter.
    """

    wildcard = "*"

    def __init__(self, *args, **kwargs):
        kwargs["lookup_expr"] = "iregex"
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        value = r"^{}$".format(value.replace(self.wildcard, ".*"))

        return super().filter(qs, value)
