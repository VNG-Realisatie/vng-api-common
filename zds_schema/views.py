import logging
import uuid
from collections import OrderedDict

from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

STATUS_TO_TITLE = {}  # TODO


def exception_handler(exc, context):
    """
    Transform 4xx and 5xx errors into DSO-compliant shape.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return

    data = getattr(response, 'data', {})

    # Get the human-readable title, from most-specific to least specific
    # because of how `drf_exception_handler` works, this is always an APIException
    # instance
    title = STATUS_TO_TITLE.get(response.status_code, exc.default_detail)

    # if we're passing an instance that the client receives, this should be
    # retrievable somewhere. Ideally, this would be in Sentry, but for now we
    # can do an attempt to put the UUID in the log files if logging is setup
    # properly.
    exc_id = str(uuid.uuid4())
    logger.exception("Exception %s ocurred", exc_id)

    response.data = OrderedDict([
        ('type', exc.__class__.__name__),
        ('title', title),
        ('status', response.status_code),
        # re-use DRFs default format to get the detail message
        ('detail', data.get('detail', '')),
        ('instance', f"urn:uuid:{exc_id}"),
    ])

    if isinstance(exc, exceptions.ValidationError):
        response.data['invalid-params'] = [
            OrderedDict([
                ('name', field_name),
                ('reason', '; '.join(message))
            ])
            # we lose the ErrorDetail instance here :/
            for field_name, message in exc.detail.items()
        ]

    return response
