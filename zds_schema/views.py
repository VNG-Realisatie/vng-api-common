import logging
import uuid
from collections import OrderedDict

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

STATUS_TO_TITLE = {}  # TODO


def _translate_exceptions(exc):
    # Taken from DRF default exc handler
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    return exc


def get_validation_errors(validation_errors: dict):
    for field_name, error_list in validation_errors.items():
        for error in error_list:
            yield OrderedDict([
                # see https://tools.ietf.org/html/rfc7807#section-3.1
                # ('type', 'about:blank'),
                ('name', field_name),
                ('code', error.code),
                ('reason', str(error)),
            ])


def exception_handler(exc, context):
    """
    Transform 4xx and 5xx errors into DSO-compliant shape.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return

    exc = _translate_exceptions(exc)

    request = context.get('request')

    data = getattr(response, 'data', {})
    error_detail = data.get('detail', '')

    # Get the human-readable title, from most-specific to least specific
    # because of how `drf_exception_handler` works, this is always an APIException
    # instance
    default_title = getattr(exc, 'default_detail', str(error_detail))
    title = STATUS_TO_TITLE.get(response.status_code, default_title)

    # if we're passing an instance that the client receives, this should be
    # retrievable somewhere. Ideally, this would be in Sentry, but for now we
    # can do an attempt to put the UUID in the log files if logging is setup
    # properly.
    exc_id = str(uuid.uuid4())
    logger.exception("Exception %s ocurred", exc_id)

    exc_detail_url = reverse(
        'zds_schema:error-detail',
        kwargs={'exception_class': exc.__class__.__name__}
    )
    if request is not None:
        exc_detail_url = request.build_absolute_uri(exc_detail_url)

    # Build the new response shape
    # TODO: use serializer, so we can use DRF-yasg serializer inspection to get
    # the schema!
    response.data = OrderedDict([
        ('type', f"URI: {exc_detail_url}"),
        # not according to DSO, but possible for programmatic checking
        ('code', error_detail.code if error_detail else ''),
        ('title', title),
        ('status', response.status_code),
        # re-use DRFs default format to get the detail message
        ('detail', str(error_detail)),
        ('instance', f"urn:uuid:{exc_id}"),
    ])

    if isinstance(exc, exceptions.ValidationError):
        response.data['code'] = exceptions.ValidationError.default_code
        response.data['invalid-params'] = [
            error for error in get_validation_errors(exc.detail)
        ]

    return response


class ErrorDetailView(TemplateView):
    template_name = 'zds_schema/error_detail.html'

    def _get_exception_klass(self):
        klass = self.kwargs['exception_class']
        try:
            return getattr(exceptions, klass)
        except AttributeError:
            raise Http404("Unknown exception class '{}'".format(klass))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exc_klass = self._get_exception_klass()
        context.update({
            'type': exc_klass.__name__,
            'status_code': exc_klass.status_code,
            'default_detail': exc_klass.default_detail,
            'default_code': exc_klass.default_code,
        })
        return context
