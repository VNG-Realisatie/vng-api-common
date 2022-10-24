import inspect
import logging

from django.apps import apps
from django.utils.translation import gettext, gettext_lazy as _

from drf_spectacular import openapi
from drf_spectacular.extensions import OpenApiFilterExtension
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_array_type,
    build_media_type_object,
    modify_media_types_for_versioning,
)
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from rest_framework import exceptions, serializers, status, viewsets

from vng_api_common.search import is_search_view
from vng_api_common.utils import underscore_to_camel

from .caching.introspection import has_cache_header
from .constants import HEADER_AUDIT, HEADER_LOGRECORD_ID, VERSION_HEADER
from .exceptions import Conflict, Gone, PreconditionFailed
from .extensions.utils import CACHE_REQUEST_HEADERS, get_cache_headers, has_geo_fields
from .geo import DEFAULT_CRS, HEADER_ACCEPT, HEADER_CONTENT, GeoMixin
from .permissions import BaseAuthRequired, get_required_scopes
from .serializers import FoutSerializer, ValidatieFoutSerializer

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

AUDIT_TRAIL_ENABLED = apps.is_installed("vng_api_common.audittrails")

AUDIT_REQUEST_HEADERS = [
    OpenApiParameter(
        name=HEADER_LOGRECORD_ID,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
        required=False,
        description=gettext(
            "Identifier of the request, traceable throughout the network"
        ),
    ),
    OpenApiParameter(
        name=HEADER_AUDIT,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
        required=False,
        description=gettext("Explanation why the request is done"),
    ),
]

version_header = "Geeft een specifieke API-versie aan in de context van een specifieke aanroep. Voorbeeld: 1.2.1."

location_header = "URL waar de resource leeft."


def _view_supports_audittrail(view: viewsets.ViewSet) -> bool:
    if not AUDIT_TRAIL_ENABLED:
        return False

    if not hasattr(view, "action"):
        logger.debug("Could not determine view action for view %r", view)
        return False

    # local imports, since you get errors if you try to import non-installed app
    # models
    from .audittrails.viewsets import AuditTrailMixin

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


def convert_parameters(parameters):
    converted_parameters = []
    type_mapping = {
        "string": OpenApiTypes.STR,
        "integer": OpenApiTypes.INT,
    }

    for parameter in parameters:
        kwargs = {}

        for key, value in parameter.items():
            if key == "in":
                location = parameter[key]
                kwargs["location"] = location
            elif key == "schema":
                type_ = value["type"]
                converted_type = type_mapping.get(type_, type_)
                kwargs.update({**value, "type": converted_type})
            else:
                kwargs[key] = value

        converted_parameters.append(OpenApiParameter(**kwargs))
    return converted_parameters


class AutoSchema(openapi.AutoSchema):
    method_mapping = {
        "get": "retrieve",
        "post": "create",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
        "head": "headers",
    }

    def get_operation(self, path, path_regex, path_prefix, method, registry):
        if method.upper() == "HEAD":
            self.view.action = "headers"

        return super().get_operation(path, path_regex, path_prefix, method, registry)

    def get_operation_id(self):
        action = self.method_mapping[self.method.lower()]
        view_action = getattr(self.view, "action", None)

        if self.method == "GET" and self._is_list_view():
            action = "list"
        # its a custom view
        elif view_action and action != view_action:
            action = self._tokenize_path()[-1]

        if self.model is not None:
            model_name = self.model._meta.model_name
            return f"{model_name}_{action}"

        return super().get_operation_id()

    def get_summary(self):
        if self.method == "HEAD":
            return _("De headers voor een specifiek(e) %(model)s opvragen ") % {
                "model": self.model._meta.verbose_name.upper()
            }
        return super().get_summary()

    def get_description(self):
        if self.method == "HEAD":
            return _("Vraag de headers op die je bij een GET request zou krijgen.")
        return super().get_description()

    def get_auth(self):
        """
        Obtains authentication classes and permissions from view. If authentication
        is known, resolve security requirement for endpoint and security definition for
        the component section.
        For custom authentication subclass ``OpenApiAuthenticationExtension``.
        """
        auths = []

        permissions = self.view.get_permissions()
        scope_permissions = [
            perm for perm in permissions if isinstance(perm, BaseAuthRequired)
        ]

        required_scopes = []
        for perm in scope_permissions:
            scopes = get_required_scopes(
                method=self.method, view=self.view, request=None
            )
            if scopes is None:
                continue
            required_scopes.append(scopes)

        if not required_scopes:
            return None  # use global security

        scopes = [str(scope) for scope in sorted(required_scopes)]

        # TODO: this should not be hardcoded
        if spectacular_settings.SECURITY:
            auths = [{list(spectacular_settings.SECURITY[0])[0]: scopes}]
        return auths

    def get_request_serializer(self):
        if is_search_view(self.view):
            serializer_class = self.view.get_search_input_serializer_class()
            return serializer_class()

        return super().get_request_serializer()

    def get_request_parameters(self):
        serializer = self.get_request_serializer()
        headers = []

        if self.method in (
            "POST",
            "PUT",
            "PATCH",
        ):
            headers.extend(
                [
                    OpenApiParameter(
                        name="Content-Type",
                        type=OpenApiTypes.STR,
                        location=OpenApiParameter.HEADER,
                        required=True,
                        enum=self.map_parsers(),
                        description=_("Content type of the request body."),
                    )
                ]
            )

        if is_search_view(self.view):
            paginator = self._get_paginator()

            filter_extension = OpenApiFilterExtension.get_match(paginator)
            if filter_extension:
                parameters = filter_extension.get_schema_operation_parameters(self)
            else:
                parameters = paginator.get_schema_operation_parameters(self.view)

            converted_parameters = convert_parameters(parameters)
            headers.extend(converted_parameters)

        if has_cache_header(self.view):
            headers.extend(CACHE_REQUEST_HEADERS)

        if _view_supports_audittrail(self.view):
            headers.extend(AUDIT_REQUEST_HEADERS)

        if has_geo_fields(serializer):
            headers.extend(
                [
                    OpenApiParameter(
                        name=HEADER_ACCEPT,
                        type=OpenApiTypes.STR,
                        location=OpenApiParameter.HEADER,
                        required=True,
                        description="Het gewenste 'Coordinate Reference System' (CRS) van de "
                        "geometrie in het antwoord (response body). Volgens de "
                        "GeoJSON spec is WGS84 de default (EPSG:4326 is "
                        "hetzelfde als WGS84).",
                        enum=[DEFAULT_CRS],
                    ),
                    OpenApiParameter(
                        name=HEADER_CONTENT,
                        type=OpenApiTypes.STR,
                        location=OpenApiParameter.HEADER,
                        description="Het 'Coordinate Reference System' (CRS) van de "
                        "geometrie in de vraag (request body). Volgens de "
                        "GeoJSON spec is WGS84 de default (EPSG:4326 is "
                        "hetzelfde als WGS84).",
                        enum=[DEFAULT_CRS],
                        required=True,
                    ),
                ]
            )

        return headers

    def get_response_parameters(self):
        serializer = self.get_request_serializer()
        headers = []

        if has_cache_header(self.view):
            headers.extend(get_cache_headers(self.view))

        if has_geo_fields(serializer):
            headers.extend(
                [
                    OpenApiParameter(
                        name=HEADER_CONTENT,
                        type=OpenApiTypes.STR,
                        location=OpenApiParameter.HEADER,
                        description="Het 'Coordinate Reference System' (CRS) van de "
                        "geometrie in de vraag (request body). Volgens de "
                        "GeoJSON spec is WGS84 de default (EPSG:4326 is "
                        "hetzelfde als WGS84).",
                        enum=[DEFAULT_CRS],
                        response=[
                            status.HTTP_200_OK,
                            status.HTTP_201_CREATED,
                            status.HTTP_204_NO_CONTENT,
                        ],
                    ),
                ]
            )

        error_responses = self.get_error_codes()

        headers.extend(
            [
                OpenApiParameter(
                    name="Location",
                    type=OpenApiTypes.URI,
                    location=OpenApiParameter.HEADER,
                    description=location_header,
                    response=[status.HTTP_201_CREATED],
                ),
                OpenApiParameter(
                    name=VERSION_HEADER,
                    type=OpenApiTypes.STR,
                    location=OpenApiParameter.HEADER,
                    description=version_header,
                    response=[
                        status.HTTP_200_OK,
                        status.HTTP_201_CREATED,
                        status.HTTP_204_NO_CONTENT,
                        *error_responses,
                    ],
                ),
            ]
        )

        return headers

    def get_override_parameters(self):
        """
        Note that request and response headers are mixed here. These are filtered
        when spectacular retrieves the available parameters for a request/response body.
        """
        return self.get_request_parameters() + self.get_response_parameters()

    def is_deprecated(self):
        return bool(
            getattr(self.view, "deprecation_message", None) or super().is_deprecated()
        )

    def _get_response_bodies(self, direction="response"):
        response_bodies = super()._get_response_bodies(direction=direction)

        self.register_error_responses(response_bodies, direction)

        for status_code, response_body in response_bodies.items():
            response_body["description"] = HTTP_STATUS_CODE_TITLES.get(int(status_code))

        return response_bodies

    def _get_response_for_code(
        self, serializer, status_code, media_types=None, direction="response"
    ):
        if (
            isinstance(serializer, serializers.Serializer)
            and is_search_view(self.view)
            and status_code == str(status.HTTP_200_OK)
        ):
            return self.get_search_response(
                serializer, status_code, media_types, direction
            )

        return super()._get_response_for_code(
            serializer, status_code, media_types=media_types, direction=direction
        )

    def get_error_codes(self):
        if not hasattr(self.view, "action") and not is_search_view(self.view):
            return []

        action = self.view.action if not is_search_view(self.view) else "create"

        general_klasses = DEFAULT_ACTION_ERRORS.get(action)
        if general_klasses is None:
            logger.debug("Unknown action %s, no default error responses added")
            return []

        exception_klasses = general_klasses[:]
        # add geo and validation errors
        has_validation_errors = self._get_filter_parameters() or any(
            issubclass(klass, exceptions.ValidationError) for klass in exception_klasses
        )
        if has_validation_errors:
            exception_klasses.append(exceptions.ValidationError)

        if isinstance(self.view, GeoMixin):
            exception_klasses.append(PreconditionFailed)

        status_codes = sorted({e.status_code for e in exception_klasses})
        return status_codes

    def register_error_responses(self, response_bodies, direction):
        error_status_codes = self.get_error_codes()

        for status_code in error_status_codes:
            serializer = (
                ValidatieFoutSerializer
                if status_code == exceptions.ValidationError.status_code
                else FoutSerializer
            )
            response_bodies[str(status_code)] = self._get_response_for_code(
                OpenApiResponse(
                    description=HTTP_STATUS_CODE_TITLES.get(int(status_code)),
                    response=serializer,
                ),
                str(status_code),
                self.map_renderers("media_type"),
                direction=direction,
            )

            component_error_response = ResolvedComponent(
                name=str(status_code),
                type="responses",
                schema=response_bodies[str(status_code)],
            )
            self.registry.register_on_missing(component_error_response)

    def get_search_response(self, serializer, status_code, media_types, direction):
        paginator = self._get_paginator()
        paginated_name = self.get_paginated_name(
            self._get_serializer_name(serializer, "response")
        )

        child_component = self.resolve_serializer(serializer, direction)
        schema = paginator.get_paginated_response_schema(
            build_array_type(child_component.ref)
        )

        component = ResolvedComponent(
            name=paginated_name,
            type=ResolvedComponent.SCHEMA,
            schema=schema,
            object=serializer,
        )

        self.registry.register_on_missing(component)

        headers = self._get_response_headers_for_code(status_code, direction)
        headers = {"headers": headers} if headers else {}

        if not media_types:
            media_types = self.map_renderers("media_type")

        media_types = modify_media_types_for_versioning(self.view, media_types)

        return {
            **headers,
            "content": {
                media_type: build_media_type_object(
                    component.ref,
                    self._get_examples(
                        serializer, direction, media_type, status_code, []
                    ),
                )
                for media_type in media_types
            },
        }

    def _get_serializer_field_meta(self, field, direction):
        meta = super()._get_serializer_field_meta(field, direction)
        title = meta.get("title")

        if title:
            return meta

        meta["title"] = underscore_to_camel(field.field_name)

        Meta = getattr(field.parent, "Meta", None)
        model = getattr(Meta, "model", None)
        if model:
            source = getattr(model, str(field.source), None)
            field = getattr(source, "field", None)

            if not field:
                return meta

            verbose_name = getattr(field, "verbose_name", None)
            meta["title"] = verbose_name if verbose_name else ""

        return meta

    def map_renderers(self, attribute):
        for renderer in self.view.get_renderers():
            if getattr(renderer, attribute, None):
                return super().map_renderers(attribute)
        return []

    @property
    def model(self):
        if hasattr(self.view, "queryset") and self.view.queryset is not None:
            return self.view.queryset.model

        if hasattr(self.view, "get_queryset"):
            qs = self.view.get_queryset()
            return qs.model
        return None
