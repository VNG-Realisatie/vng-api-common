import inspect
import logging
from typing import Dict, List, Optional, Type

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from drf_spectacular import openapi
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiTypes
from rest_framework import exceptions, serializers, viewsets

from vng_api_common.caching.introspection import has_cache_header
from vng_api_common.constants import HEADER_AUDIT, HEADER_LOGRECORD_ID, VERSION_HEADER
from vng_api_common.exceptions import Conflict, Gone, PreconditionFailed
from vng_api_common.geo import DEFAULT_CRS, HEADER_ACCEPT, HEADER_CONTENT, GeoMixin
from vng_api_common.permissions import AuthRequired, get_required_scopes
from vng_api_common.serializers import FoutSerializer, ValidatieFoutSerializer

logger = logging.getLogger(__name__)

TYPE_TO_FIELDMAPPING = {
    OpenApiTypes.INT: serializers.IntegerField,
    OpenApiTypes.NUMBER: serializers.FloatField,
    OpenApiTypes.STR: serializers.CharField,
    OpenApiTypes.BOOL: serializers.BooleanField,
}

COMMON_ERRORS = [
    exceptions.AuthenticationFailed,
    exceptions.NotAuthenticated,
    exceptions.PermissionDenied,
    exceptions.NotAcceptable,
    Conflict,
    Gone,
    exceptions.UnsupportedMediaType,
    exceptions.Throttled,
    exceptions.APIException,
]

DEFAULT_ACTION_ERRORS = {
    "create": COMMON_ERRORS + [exceptions.ParseError, exceptions.ValidationError],
    "list": COMMON_ERRORS,
    "retrieve": COMMON_ERRORS + [exceptions.NotFound],
    "update": COMMON_ERRORS
    + [exceptions.ParseError, exceptions.ValidationError, exceptions.NotFound],
    "partial_update": COMMON_ERRORS
    + [exceptions.ParseError, exceptions.ValidationError, exceptions.NotFound],
    "destroy": COMMON_ERRORS + [exceptions.NotFound],
}

AUDIT_TRAIL_ENABLED = apps.is_installed("vng_api_common.audittrails")


def _view_supports_audittrail(view: viewsets.ViewSet) -> bool:
    if not AUDIT_TRAIL_ENABLED:
        return False

    if not hasattr(view, "action"):
        logger.debug("Could not determine view action for view %r", view)
        return False

    # local imports, since you get errors if you try to import non-installed app
    # models
    from vng_api_common.audittrails.viewsets import AuditTrailMixin

    relevant_bases = [
        base for base in view.__class__.__bases__ if issubclass(base, AuditTrailMixin)
    ]
    if not relevant_bases:
        return False

    # check if the view action is listed in any of the audit trail mixins
    action = view.action
    if action == "partial_update":  # partial update is self.update(partial=True)
        action = "update"

    # if the current view action is not provided by any of the audit trail
    # related bases, then it's not audit trail enabled
    action_in_audit_bases = any(
        action in dict(inspect.getmembers(base)) for base in relevant_bases
    )

    return action_in_audit_bases


class AutoSchema(openapi.AutoSchema):
    method_mapping = dict(
        **openapi.AutoSchema.method_mapping,
        head="headers",
    )

    def get_auth(self) -> List[Dict[str, List[str]]]:
        """
        Return a list of security requirements for this operation.

        `OpenApiAuthenticationExtension` can't be used here since it's tightly coupled
        with DRF authentication classes, and we have none in Open Zaak
        """
        permissions = self.view.get_permissions()
        scope_permissions = [
            perm for perm in permissions if isinstance(perm, AuthRequired)
        ]

        if not scope_permissions:
            return super().get_auth()

        scopes = get_required_scopes(self.view.request, self.view)
        if not scopes:
            return []

        return [{settings.SECURITY_DEFINITION_NAME: [str(scopes)]}]

    def get_override_parameters(self):
        params = super().get_override_parameters()

        # Require Content-Type headers on POST requests
        if self.method == "POST":
            mime_type_enum = [
                cls.media_type
                for cls in self.view.parser_classes
                if hasattr(cls, "media_type")
            ]
            if mime_type_enum:
                params.append(
                    OpenApiParameter(
                        name="Content-Type",
                        location=OpenApiParameter.HEADER,
                        required=True,
                        type=str,
                        enum=mime_type_enum,
                        description=_("Content type of the request body."),
                    )
                )
        return params

    def get_operation_id(self):
        """
        Use view basename as a base for operation_id
        """
        if hasattr(self.view, "basename"):
            basename = self.view.basename
            action = "head" if self.method == "HEAD" else self.view.action
            # make compatible with old OAS
            if action == "destroy":
                action = "delete"
            elif action == "retrieve":
                action = "read"

            return f"{basename}_{action}"
        return super().get_operation_id()

    def get_error_responses(self) -> Dict[int, Type[serializers.Serializer]]:
        """
        return dictionary of error codes and correspondent error serializers
        - define status codes based on exceptions for each endpoint
        - define error serializers based on status code
        """

        # only supports viewsets
        action = getattr(self.view, "action", None)
        if not action:
            return {}

        # define status codes for the action based on potential exceptions
        # general errors
        general_klasses = DEFAULT_ACTION_ERRORS.get(action)
        if general_klasses is None:
            logger.debug("Unknown action %s, no default error responses added")
            return {}

        exception_klasses = general_klasses[:]
        # add geo and validation errors
        has_validation_errors = action == "list" or any(
            issubclass(klass, exceptions.ValidationError) for klass in exception_klasses
        )
        if has_validation_errors:
            exception_klasses.append(exceptions.ValidationError)

        if isinstance(self.view, GeoMixin):
            exception_klasses.append(PreconditionFailed)

        status_codes = sorted({e.status_code for e in exception_klasses})

        # choose serializer based on the status code
        responses = {}
        for status_code in status_codes:
            error_serializer = (
                ValidatieFoutSerializer
                if status_code == exceptions.ValidationError.status_code
                else FoutSerializer
            )
            responses[status_code] = error_serializer

        return responses

    def get_response_serializers(
        self,
    ) -> Dict[int, Optional[Type[serializers.Serializer]]]:
        """append error serializers"""
        response_serializers = super().get_response_serializers()

        if self.method == "HEAD":
            return {200: None}

        if self.method == "DELETE":
            status_code = 204
            serializer = None
        elif self._is_create_operation():
            status_code = 201
            serializer = response_serializers
        else:
            status_code = 200
            serializer = response_serializers

        responses = {
            status_code: serializer,
            **self.get_error_responses(),
        }
        return responses

    def get_version_headers(self) -> List[OpenApiParameter]:
        return [
            OpenApiParameter(
                name=VERSION_HEADER,
                type=str,
                location=OpenApiParameter.HEADER,
                description=_(
                    "Geeft een specifieke API-versie aan in de context van "
                    "een specifieke aanroep. Voorbeeld: 1.2.1."
                ),
                response=True,
            )
        ]

    def get_content_type_headers(self) -> List[OpenApiParameter]:
        if self.method not in ["POST", "PUT", "PATCH"]:
            return []

        return [
            OpenApiParameter(
                name="Content-Type",
                type=str,
                location=OpenApiParameter.HEADER,
                description=_("Content type of the request body."),
                enum=["application/json"],
                required=True,
            )
        ]

    def get_cache_headers(self) -> List[OpenApiParameter]:
        """
        support ETag headers
        """
        if not has_cache_header(self.view):
            return []

        return [
            OpenApiParameter(
                name="If-None-Match",
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description=_(
                    "Perform conditional requests. This header should contain one or "
                    "multiple ETag values of resources the client has cached. If the "
                    "current resource ETag value is in this set, then an HTTP 304 "
                    "empty body will be returned. See "
                    "[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match) "
                    "for details."
                ),
                examples=[
                    OpenApiExample(
                        name="oneValue",
                        summary=_("One ETag value"),
                        value='"79054025255fb1a26e4bc422aef54eb4"',
                    ),
                    OpenApiExample(
                        name="multipleValues",
                        summary=_("Multiple ETag values"),
                        value='"79054025255fb1a26e4bc422aef54eb4", "e4d909c290d0fb1ca068ffaddf22cbd0"',
                    ),
                ],
            ),
            OpenApiParameter(
                name="ETag",
                type=str,
                location=OpenApiParameter.HEADER,
                response=[200],
                description=_(
                    "De ETag berekend op de response body JSON. "
                    "Indien twee resources exact dezelfde ETag hebben, dan zijn "
                    "deze resources identiek aan elkaar. Je kan de ETag gebruiken "
                    "om caching te implementeren."
                ),
            ),
        ]

    def get_location_headers(self) -> List[OpenApiParameter]:
        return [
            OpenApiParameter(
                name="Location",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.HEADER,
                description=_("URL waar de resource leeft."),
                response=[201],
            ),
        ]

    def get_geo_headers(self) -> List[OpenApiParameter]:
        if not isinstance(self.view, GeoMixin):
            return []

        request_headers = []
        if self.method != "DELETE":
            request_headers.append(
                OpenApiParameter(
                    name=HEADER_ACCEPT,
                    type=str,
                    location=OpenApiParameter.HEADER,
                    required=False,
                    description=_(
                        "The desired 'Coordinate Reference System' (CRS) of the response data. "
                        "According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 "
                        "is the same as WGS84)."
                    ),
                    enum=[DEFAULT_CRS],
                )
            )

        if self.method in ("POST", "PUT", "PATCH"):
            request_headers.append(
                OpenApiParameter(
                    name=HEADER_CONTENT,
                    type=str,
                    location=OpenApiParameter.HEADER,
                    required=True,
                    description=_(
                        "The 'Coordinate Reference System' (CRS) of the request data. "
                        "According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 "
                        "is the same as WGS84)."
                    ),
                    enum=[DEFAULT_CRS],
                ),
            )

        response_headers = [
            OpenApiParameter(
                name=HEADER_CONTENT,
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description=_(
                    "The 'Coordinate Reference System' (CRS) of the request data. "
                    "According to the GeoJSON spec, WGS84 is the default (EPSG: 4326 "
                    "is the same as WGS84)."
                ),
                enum=[DEFAULT_CRS],
                response=[200, 201],
            )
        ]

        return request_headers + response_headers

    def get_log_headers(self) -> List[OpenApiParameter]:
        if not _view_supports_audittrail(self.view):
            return []

        return [
            OpenApiParameter(
                name=HEADER_LOGRECORD_ID,
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description=_(
                    "Identifier of the request, traceable throughout the network"
                ),
            ),
            OpenApiParameter(
                name=HEADER_AUDIT,
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description=_("Explanation why the request is done"),
            ),
        ]

    def get_override_parameters(self):
        """Add request and response headers"""
        version_headers = self.get_version_headers()
        content_type_headers = self.get_content_type_headers()
        cache_headers = self.get_cache_headers()
        log_headers = self.get_log_headers()
        location_headers = self.get_location_headers()
        geo_headers = self.get_geo_headers()
        return (
            version_headers
            + content_type_headers
            + cache_headers
            + log_headers
            + location_headers
            + geo_headers
        )
