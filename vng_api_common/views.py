from collections import OrderedDict

from django.apps import apps
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

import requests
from rest_framework import exceptions as drf_exceptions
from rest_framework.views import exception_handler as drf_exception_handler
from zds_client import ClientError

from . import exceptions
from .exception_handling import HandledException
from .scopes import SCOPE_REGISTRY

ERROR_CONTENT_TYPE = 'application/problem+json'


def exception_handler(exc, context):
    """
    Transform 4xx and 5xx errors into DSO-compliant shape.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return

    request = context.get('request')

    serializer = HandledException.as_serializer(exc, response, request)
    response.data = OrderedDict(serializer.data.items())
    # custom content type
    response['Content-Type'] = ERROR_CONTENT_TYPE
    return response


class ErrorDetailView(TemplateView):
    template_name = 'vng_api_common/ref/error_detail.html'

    def _get_exception_klass(self):
        klass = self.kwargs['exception_class']

        for module in [exceptions, drf_exceptions]:
            exc_klass = getattr(module, klass, None)
            if exc_klass is not None:
                return exc_klass
        else:
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


class ScopesView(TemplateView):
    template_name = 'vng_api_common/ref/scopes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scopes'] = sorted(
            (scope for scope in SCOPE_REGISTRY if not scope.children),
            key=lambda s: s.label
        )
        return context


class ViewConfigView(TemplateView):
    template_name = 'vng_api_common/view_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        config = []
        config += _test_ac_config()

        context['config'] = config

        return context


def _test_ac_config() -> list:
    if not apps.is_installed('vng_api_common.authorizations'):
        return []

    from .authorizations.models import AuthorizationsConfig

    auth_config = AuthorizationsConfig.get_solo()

    # check if AC auth is configured
    ac_client = AuthorizationsConfig.get_client()
    has_ac_auth = ac_client.auth is not None

    checks = [
        (_("Type of component"), auth_config.get_component_display(), None),
        (_("AC"), auth_config.api_root, bool(auth_config.api_root)),
        (
            _("Credentials for AC"),
            _("Configured") if has_ac_auth else _("Missing"),
            has_ac_auth
        ),
    ]

    # check if permissions in AC are fine
    if has_ac_auth:
        error = False

        try:
            ac_client.list(
                "applicatie",
                query_params={"clientIds": ac_client.auth.client_id}
            )
        except requests.ConnectionError:
            error = True
            message = _("Could not connect with AC")
        except ClientError as exc:
            error = True
            message = _("Cannot retrieve authorizations: HTTP {status_code} - {error_code}").format(
                status_code=exc.args[0]['status'],
                error_code=exc.args[0]['code']
            )
        else:
            message = _("Can retrieve authorizations")

        checks.append((
            _("AC connection and authorizations"),
            message,
            not error,
        ))

    return checks
