import logging
from typing import Dict, List, Optional, Type

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from drf_spectacular import openapi
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiTypes
from rest_framework import exceptions, serializers, status

from .audittrails.utils import _view_supports_audittrail
from .caching.introspection import has_cache_header
from .constants import HEADER_AUDIT, HEADER_LOGRECORD_ID, VERSION_HEADER
from .exceptions import Conflict, Gone, PreconditionFailed
from .geo import DEFAULT_CRS, HEADER_ACCEPT, HEADER_CONTENT, GeoMixin
from .permissions import BaseAuthRequired, get_required_scopes
from .serializers import FoutSerializer, ValidatieFoutSerializer
from .views import ERROR_CONTENT_TYPE

logger = logging.getLogger(__name__)

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

HTTP_STATUS_CODE_TITLES = {
    status.HTTP_100_CONTINUE: "Continue",
    status.HTTP_101_SWITCHING_PROTOCOLS: "Switching protocols",
    status.HTTP_200_OK: "OK",
    status.HTTP_201_CREATED: "Created",
    status.HTTP_202_ACCEPTED: "Accepted",
    status.HTTP_203_NON_AUTHORITATIVE_INFORMATION: "Non authoritative information",
    status.HTTP_204_NO_CONTENT: "No content",
    status.HTTP_205_RESET_CONTENT: "Reset content",
    status.HTTP_206_PARTIAL_CONTENT: "Partial content",
    status.HTTP_207_MULTI_STATUS: "Multi status",
    status.HTTP_300_MULTIPLE_CHOICES: "Multiple choices",
    status.HTTP_301_MOVED_PERMANENTLY: "Moved permanently",
    status.HTTP_302_FOUND: "Found",
    status.HTTP_303_SEE_OTHER: "See other",
    status.HTTP_304_NOT_MODIFIED: "Not modified",
    status.HTTP_305_USE_PROXY: "Use proxy",
    status.HTTP_306_RESERVED: "Reserved",
    status.HTTP_307_TEMPORARY_REDIRECT: "Temporary redirect",
    status.HTTP_400_BAD_REQUEST: "Bad request",
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_402_PAYMENT_REQUIRED: "Payment required",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method not allowed",
    status.HTTP_406_NOT_ACCEPTABLE: "Not acceptable",
    status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED: "Proxy authentication required",
    status.HTTP_408_REQUEST_TIMEOUT: "Request timeout",
    status.HTTP_409_CONFLICT: "Conflict",
    status.HTTP_410_GONE: "Gone",
    status.HTTP_411_LENGTH_REQUIRED: "Length required",
    status.HTTP_412_PRECONDITION_FAILED: "Precondition failed",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "Request entity too large",
    status.HTTP_414_REQUEST_URI_TOO_LONG: "Request uri too long",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "Unsupported media type",
    status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: "Requested range not satisfiable",
    status.HTTP_417_EXPECTATION_FAILED: "Expectation failed",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Unprocessable entity",
    status.HTTP_423_LOCKED: "Locked",
    status.HTTP_424_FAILED_DEPENDENCY: "Failed dependency",
    status.HTTP_428_PRECONDITION_REQUIRED: "Precondition required",
    status.HTTP_429_TOO_MANY_REQUESTS: "Too many requests",
    status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE: "Request header fields too large",
    status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS: "Unavailable for legal reasons",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal server error",
    status.HTTP_501_NOT_IMPLEMENTED: "Not implemented",
    status.HTTP_502_BAD_GATEWAY: "Bad gateway",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Service unavailable",
    status.HTTP_504_GATEWAY_TIMEOUT: "Gateway timeout",
    status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED: "HTTP version not supported",
    status.HTTP_507_INSUFFICIENT_STORAGE: "Insufficient storage",
    status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED: "Network authentication required",
}


class AutoSchema(openapi.AutoSchema):
    method_mapping = dict(
        **openapi.AutoSchema.method_mapping,
        head="headers",
    )

    def get_auth(self) -> List[Dict[str, List[str]]]:
        """
        Return a list of security requirements for this operation.

        `OpenApiAuthenticationExtension` can't be used here since it's tightly coupled
        with DRF authentication classes
        """
        permissions = self.view.get_permissions()
        scope_permissions = [
            perm for perm in permissions if isinstance(perm, BaseAuthRequired)
        ]

        if not scope_permissions:
            return super().get_auth()

        scopes = get_required_scopes(self.view.request, self.view)
        if not scopes:
            return []

        return [{settings.SECURITY_DEFINITION_NAME: [str(scopes)]}]

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

    def _get_response_for_code(
        self, serializer, status_code, media_types=None, direction="response"
    ):
        """
        choose media types and set descriptions
        add custom response for expand
        """
        if not media_types:
            if int(status_code) >= 400:
                media_types = [ERROR_CONTENT_TYPE]
            else:
                media_types = ["application/json"]

        response = super()._get_response_for_code(
            serializer, status_code, media_types, direction
        )

        # add description based on the status code
        if not response.get("description"):
            response["description"] = HTTP_STATUS_CODE_TITLES.get(int(status_code), "")
        return response

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

        mime_type_enum = [
            cls.media_type
            for cls in self.view.parser_classes
            if hasattr(cls, "media_type")
        ]

        return [
            OpenApiParameter(
                name="Content-Type",
                type=str,
                location=OpenApiParameter.HEADER,
                description=_("Content type of the request body."),
                enum=mime_type_enum,
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

    def get_summary(self):
        if self.method == "HEAD":
            return _("De headers voor een specifiek(e) %(model)s opvragen ") % {
                "model": self.view.queryset.model._meta.verbose_name.upper()
            }
        return super().get_summary()

    def get_description(self):
        if self.method == "HEAD":
            return _("Vraag de headers op die je bij een GET request zou krijgen.")
        return super().get_description()
