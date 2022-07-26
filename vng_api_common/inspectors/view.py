import inspect
import logging
from collections import OrderedDict
from itertools import chain
from typing import Optional, Tuple, Union

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext, gettext_lazy as _

from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import get_consumes
from rest_framework import exceptions, serializers, status, viewsets

from ..constants import HEADER_AUDIT, HEADER_LOGRECORD_ID, VERSION_HEADER
from ..exceptions import Conflict, Gone, PreconditionFailed
from ..geo import GeoMixin
from ..permissions import BaseAuthRequired, get_required_scopes
from ..search import is_search_view
from ..serializers import (
    FoutSerializer,
    ValidatieFoutSerializer,
    add_choice_values_help_text,
)
from .cache import CACHE_REQUEST_HEADERS, get_cache_headers, has_cache_header

logger = logging.getLogger(__name__)

TYPE_TO_FIELDMAPPING = {
    openapi.TYPE_INTEGER: serializers.IntegerField,
    openapi.TYPE_NUMBER: serializers.FloatField,
    openapi.TYPE_STRING: serializers.CharField,
    openapi.TYPE_BOOLEAN: serializers.BooleanField,
    openapi.TYPE_ARRAY: serializers.ListField,
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
    openapi.Parameter(
        name=HEADER_LOGRECORD_ID,
        type=openapi.TYPE_STRING,
        in_=openapi.IN_HEADER,
        required=False,
        description=gettext(
            "Identifier of the request, traceable throughout the network"
        ),
    ),
    openapi.Parameter(
        name=HEADER_AUDIT,
        type=openapi.TYPE_STRING,
        in_=openapi.IN_HEADER,
        required=False,
        description=gettext("Explanation why the request is done"),
    ),
]


def response_header(description: str, type: str, format: str = None) -> OrderedDict:
    header = OrderedDict(
        (("schema", OrderedDict((("type", type),))), ("description", description))
    )
    if format is not None:
        header["schema"]["format"] = format
    return header


version_header = response_header(
    "Geeft een specifieke API-versie aan in de context van een specifieke aanroep. Voorbeeld: 1.2.1.",
    type=openapi.TYPE_STRING,
)

location_header = response_header(
    "URL waar de resource leeft.", type=openapi.TYPE_STRING, format=openapi.FORMAT_URI
)


def _view_supports_audittrail(view: viewsets.ViewSet) -> bool:
    if not AUDIT_TRAIL_ENABLED:
        return False

    if not hasattr(view, "action"):
        logger.debug("Could not determine view action for view %r", view)
        return False

    # local imports, since you get errors if you try to import non-installed app
    # models
    from ..audittrails.viewsets import AuditTrailMixin

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


class ResponseRef(openapi._Ref):
    def __init__(self, resolver, response_name, ignore_unresolved=False):
        """
        Adds a reference to a named Response defined in the ``#/responses/`` object.
        """
        assert "responses" in resolver.scopes
        super().__init__(
            resolver, response_name, "responses", openapi.Response, ignore_unresolved
        )


class AutoSchema(SwaggerAutoSchema):
    @property
    def model(self):
        if hasattr(self.view, "queryset") and self.view.queryset is not None:
            return self.view.queryset.model

        if hasattr(self.view, "get_queryset"):
            qs = self.view.get_queryset()
            return qs.model
        return None

    @property
    def _is_search_view(self):
        return is_search_view(self.view)

    def get_operation_id(self, operation_keys=None) -> str:
        """
        Simply return the model name as lowercase string, postfixed with the operation name.
        """
        operation_keys = operation_keys or self.operation_keys

        operation_id = self.overrides.get("operation_id", "")
        if operation_id:
            return operation_id

        action = operation_keys[-1]
        if self.model is not None:
            model_name = self.model._meta.model_name
            return f"{model_name}_{action}"
        else:
            operation_id = "_".join(operation_keys)
            return operation_id

    def should_page(self):
        if self._is_search_view:
            return hasattr(self.view, "paginator")
        return super().should_page()

    def get_request_serializer(self):
        if not self._is_search_view:
            return super().get_request_serializer()

        Base = self.view.get_search_input_serializer_class()

        filter_fields = []
        for filter_backend in self.view.filter_backends:
            filter_fields += (
                self.probe_inspectors(
                    self.filter_inspectors, "get_filter_parameters", filter_backend()
                )
                or []
            )

        filters = {}
        for parameter in filter_fields:
            help_text = parameter.description
            # we can't get the verbose_label back from the enum, so the inspector
            # in vng_api_common.inspectors.fields leaves a filter field reference behind
            _filter_field = getattr(parameter, "_filter_field", None)
            choices = getattr(_filter_field, "extra", {}).get("choices", [])
            if choices:
                FieldClass = serializers.ChoiceField
                extra = {"choices": choices}
                value_display_mapping = add_choice_values_help_text(choices)
                help_text += f"\n\n{value_display_mapping}"
            else:
                FieldClass = TYPE_TO_FIELDMAPPING[parameter.type]
                extra = {}

            filters[parameter.name] = FieldClass(
                help_text=help_text, required=parameter.required, **extra
            )

        SearchSerializer = type(Base.__name__, (Base,), filters)
        return SearchSerializer()

    def _get_search_responses(self):
        response_status = status.HTTP_200_OK
        response_schema = self.serializer_to_schema(self.get_view_serializer())
        schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=response_schema)
        if self.should_page():
            schema = self.get_paginated_response(schema) or schema
        return OrderedDict({str(response_status): schema})

    def register_error_responses(self):
        ref_responses = self.components.with_scope("responses")

        if not ref_responses.keys():
            # general errors
            general_classes = list(chain(*DEFAULT_ACTION_ERRORS.values()))
            # add geo and validation errors
            exception_classes = general_classes + [
                PreconditionFailed,
                exceptions.ValidationError,
            ]
            status_codes = sorted({e.status_code for e in exception_classes})

            fout_schema = self.serializer_to_schema(FoutSerializer())
            validation_fout_schema = self.serializer_to_schema(
                ValidatieFoutSerializer()
            )
            for status_code in status_codes:
                schema = (
                    validation_fout_schema
                    if status_code == exceptions.ValidationError.status_code
                    else fout_schema
                )
                response = openapi.Response(
                    description=HTTP_STATUS_CODE_TITLES.get(status_code, ""),
                    schema=schema,
                )
                self.set_response_headers(str(status_code), response)
                ref_responses.set(str(status_code), response)

    def _get_error_responses(self) -> OrderedDict:
        """
        Add the appropriate possible error responses to the schema.

        E.g. - we know that HTTP 400 on a POST/PATCH/PUT leads to validation
        errors, 403 to Permission Denied etc.
        """
        # only supports viewsets
        if not hasattr(self.view, "action"):
            return OrderedDict()

        self.register_error_responses()

        action = self.view.action
        if (
            action not in DEFAULT_ACTION_ERRORS and self._is_search_view
        ):  # similar to a CREATE
            action = "create"

        # general errors
        general_klasses = DEFAULT_ACTION_ERRORS.get(action)
        if general_klasses is None:
            logger.debug("Unknown action %s, no default error responses added")
            return OrderedDict()

        exception_klasses = general_klasses[:]
        # add geo and validation errors
        has_validation_errors = self.get_filter_parameters() or any(
            issubclass(klass, exceptions.ValidationError) for klass in exception_klasses
        )
        if has_validation_errors:
            exception_klasses.append(exceptions.ValidationError)

        if isinstance(self.view, GeoMixin):
            exception_klasses.append(PreconditionFailed)

        status_codes = sorted({e.status_code for e in exception_klasses})

        return OrderedDict(
            [
                (status_code, ResponseRef(self.components, str(status_code)))
                for status_code in status_codes
            ]
        )

    def get_default_responses(self) -> OrderedDict:
        if self._is_search_view:
            responses = self._get_search_responses()
            serializer = self.get_view_serializer()
        else:
            responses = super().get_default_responses()
            serializer = self.get_request_serializer() or self.get_view_serializer()

        # inject any headers
        _responses = OrderedDict()
        custom_headers = OrderedDict()
        for status_, schema in responses.items():
            if serializer is not None:
                custom_headers = (
                    self.probe_inspectors(
                        self.field_inspectors,
                        "get_response_headers",
                        serializer,
                        {"field_inspectors": self.field_inspectors},
                        status=status_,
                    )
                    or OrderedDict()
                )

            # add the cache headers, if applicable
            for header, header_schema in get_cache_headers(self.view).items():
                custom_headers[header] = header_schema

            assert isinstance(schema, openapi.Schema.OR_REF) or schema == ""
            response = openapi.Response(
                description=HTTP_STATUS_CODE_TITLES.get(int(status_), ""),
                schema=schema or None,
                headers=custom_headers,
            )
            _responses[status_] = response

        for status_code, response in self._get_error_responses().items():
            _responses[status_code] = response

        return _responses

    @staticmethod
    def set_response_headers(
        status_code: str, response: Union[openapi.Response, ResponseRef]
    ):
        if not isinstance(response, openapi.Response):
            return

        response.setdefault("headers", OrderedDict())
        response["headers"][VERSION_HEADER] = version_header

        if status_code == "201":
            response["headers"]["Location"] = location_header

    def get_response_schemas(self, response_serializers):
        # parent class doesn't support responses as ref objects,
        # so we temporary remove them
        ref_responses = OrderedDict()
        for status_code, serializer in response_serializers.copy().items():
            if isinstance(serializer, ResponseRef):
                ref_responses[str(status_code)] = response_serializers.pop(status_code)

        responses = super().get_response_schemas(response_serializers)

        # and add them again
        responses.update(ref_responses)
        responses = OrderedDict(sorted(responses.items()))

        # add the Api-Version headers
        for status_code, response in responses.items():
            self.set_response_headers(status_code, response)

        return responses

    def get_request_content_type_header(self) -> Optional[openapi.Parameter]:
        if self.method not in ["POST", "PUT", "PATCH"]:
            return None

        consumes = get_consumes(self.get_parser_classes())
        return openapi.Parameter(
            name="Content-Type",
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            required=True,
            enum=consumes,
            description=_("Content type of the request body."),
        )

    def add_manual_parameters(self, parameters):
        base = super().add_manual_parameters(parameters)

        content_type = self.get_request_content_type_header()
        if content_type is not None:
            base = [content_type] + base

        if self._is_search_view:
            serializer = self.get_request_serializer()
        else:
            serializer = self.get_request_serializer() or self.get_view_serializer()

        extra = []
        if serializer is not None:
            extra = (
                self.probe_inspectors(
                    self.field_inspectors,
                    "get_request_header_parameters",
                    serializer,
                    {"field_inspectors": self.field_inspectors},
                )
                or []
            )
        result = base + extra

        if has_cache_header(self.view):
            result += CACHE_REQUEST_HEADERS

        if _view_supports_audittrail(self.view):
            result += AUDIT_REQUEST_HEADERS

        return result

    def get_security(self):
        """Return a list of security requirements for this operation.

        Returning an empty list marks the endpoint as unauthenticated (i.e. removes all accepted
        authentication schemes). Returning ``None`` will inherit the top-level secuirty requirements.

        :return: security requirements
        :rtype: list[dict[str,list[str]]]"""
        permissions = self.view.get_permissions()
        scope_permissions = [
            perm for perm in permissions if isinstance(perm, BaseAuthRequired)
        ]

        if not scope_permissions:
            return super().get_security()

        if len(permissions) != len(scope_permissions):
            logger.warning(
                "Can't represent all permissions in OAS for path %s and method %s",
                self.path,
                self.method,
            )

        required_scopes = []
        for perm in scope_permissions:
            scopes = get_required_scopes(self.request, self.view)
            if scopes is None:
                continue
            required_scopes.append(scopes)

        if not required_scopes:
            return None  # use global security

        scopes = [str(scope) for scope in sorted(required_scopes)]

        # operation level security
        return [{settings.SECURITY_DEFINITION_NAME: scopes}]

    # all of these break if you accept method HEAD because the view.action is None
    def is_list_view(self) -> bool:
        if self.method == "HEAD":
            return False
        return super().is_list_view()

    def get_summary_and_description(self) -> Tuple[str, str]:
        if self.method != "HEAD":
            return super().get_summary_and_description()

        default_description = _(
            "De headers voor een specifiek(e) {model_name} opvragen"
        ).format(model_name=self.model._meta.model_name.upper())
        default_summary = _(
            "Vraag de headers op die je bij een GET request zou krijgen."
        )

        description = self.overrides.get("operation_description", default_description)
        summary = self.overrides.get("operation_summary", default_summary)
        return description, summary

    # patch around drf-yasg not taking overrides into account
    # TODO: contribute back in PR
    def get_produces(self) -> list:
        produces = super().get_produces()
        return self.overrides.get("produces", produces)


# translations aren't picked up/defined in DRF, so we need to hook them up here
_("A page number within the paginated result set.")
_("Number of results to return per page.")
