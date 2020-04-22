import logging
import os
from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.http import Http404, HttpRequest
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

import requests
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from zds_client import ClientError

from . import exceptions
from .compat import sentry_client
from .constants import ComponentTypes
from .exception_handling import HandledException
from .scopes import SCOPE_REGISTRY

logger = logging.getLogger(__name__)

ERROR_CONTENT_TYPE = "application/problem+json"


def exception_handler(exc, context):
    """
    Transform 4xx and 5xx errors into DSO-compliant shape.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        if os.getenv("DEBUG", "").lower() in ["yes", "1", "true"]:
            return None

        logger.exception(exc.args[0], exc_info=1)
        # make sure the exception still ends up in Sentry
        sentry_client.captureException()

        # unkown type, so we use the generic Internal Server Error
        exc = drf_exceptions.APIException("Internal Server Error")
        response = Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    request = context.get("request")

    serializer = HandledException.as_serializer(exc, response, request)
    response.data = OrderedDict(serializer.data.items())
    # custom content type
    response["Content-Type"] = ERROR_CONTENT_TYPE
    return response


class ErrorDetailView(TemplateView):
    template_name = "vng_api_common/ref/error_detail.html"

    def _get_exception_klass(self):
        klass = self.kwargs["exception_class"]

        for module in [exceptions, drf_exceptions]:
            exc_klass = getattr(module, klass, None)
            if exc_klass is not None:
                return exc_klass
        else:
            raise Http404("Unknown exception class '{}'".format(klass))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exc_klass = self._get_exception_klass()
        context.update(
            {
                "type": exc_klass.__name__,
                "status_code": exc_klass.status_code,
                "default_detail": exc_klass.default_detail,
                "default_code": exc_klass.default_code,
            }
        )
        return context


class ScopesView(TemplateView):
    template_name = "vng_api_common/ref/scopes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scopes"] = sorted(
            (scope for scope in SCOPE_REGISTRY if not scope.children),
            key=lambda s: s.label,
        )
        return context


class ViewConfigView(TemplateView):
    template_name = "vng_api_common/view_config.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        config = []
        config += _test_sites_config(self.request)
        config += _test_ac_config()
        config += _test_nrc_config()

        context["config"] = config

        return context


def _test_sites_config(request: HttpRequest) -> list:
    if not apps.is_installed("django.contrib.sites"):
        return []

    from django.contrib.sites.models import Site

    site = Site.objects.get_current()

    return [
        (_("Site domain"), site.domain, request.get_host() == site.domain),
        (_("HTTPS"), settings.IS_HTTPS, settings.IS_HTTPS == request.is_secure()),
    ]


def _test_ac_config() -> list:
    if not apps.is_installed("vng_api_common.authorizations"):
        return []

    from .authorizations.models import AuthorizationsConfig

    auth_config = AuthorizationsConfig.get_solo()

    # check if AC auth is configured
    ac_client = AuthorizationsConfig.get_client()
    has_ac_auth = ac_client.auth is not None

    checks = [
        (_("Type of component"), auth_config.get_component_display(), None),
        (_("AC"), auth_config.api_root, auth_config.api_root.endswith("/")),
        (
            _("Credentials for AC"),
            _("Configured") if has_ac_auth else _("Missing"),
            has_ac_auth,
        ),
    ]

    # check if permissions in AC are fine
    if has_ac_auth:
        error = False

        try:
            ac_client.list(
                "applicatie", query_params={"clientIds": ac_client.auth.client_id}
            )
        except requests.ConnectionError:
            error = True
            message = _("Could not connect with AC")
        except ClientError as exc:
            error = True
            message = _(
                "Cannot retrieve authorizations: HTTP {status_code} - {error_code}"
            ).format(status_code=exc.args[0]["status"], error_code=exc.args[0]["code"])
        else:
            message = _("Can retrieve authorizations")

        checks.append((_("AC connection and authorizations"), message, not error))

    return checks


def _test_nrc_config() -> list:
    if not apps.is_installed("vng_api_common.notifications"):
        return []

    from .notifications.models import NotificationsConfig, Subscription

    nrc_config = NotificationsConfig.get_solo()

    nrc_client = NotificationsConfig.get_client()

    has_nrc_auth = nrc_client.auth is not None

    checks = [
        (_("NRC"), nrc_config.api_root, nrc_config.api_root.endswith("/")),
        (
            _("Credentials for NRC"),
            _("Configured") if has_nrc_auth else _("Missing"),
            has_nrc_auth,
        ),
    ]

    # check if permissions in AC are fine
    if has_nrc_auth:
        error = False

        try:
            nrc_client.list("kanaal")
        except requests.ConnectionError:
            error = True
            message = _("Could not connect with NRC")
        except ClientError as exc:
            error = True
            message = _(
                "Cannot retrieve kanalen: HTTP {status_code} - {error_code}"
            ).format(status_code=exc.args[0]["status"], error_code=exc.args[0]["code"])
        else:
            message = _("Can retrieve kanalen")

        checks.append((_("NRC connection and authorizations"), message, not error))

    #  check if there's a subscription for AC notifications
    has_sub = (
        Subscription.objects.filter(channels__contains=["autorisaties"])
        .exclude(_subscription="")
        .exists()
    )
    check_ok = has_sub

    if apps.is_installed("vng_api_common.authorizations"):
        from .authorizations.models import AuthorizationsConfig

        auth_config = AuthorizationsConfig.get_solo()
        if auth_config.component == ComponentTypes.ac and not has_sub:
            check_ok = True

    checks.append(
        (_("Listens to AC notifications?"), _("Yes") if has_sub else _("No"), check_ok)
    )

    return checks
