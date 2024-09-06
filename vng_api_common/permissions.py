import logging
import time
from typing import TYPE_CHECKING, Any, Dict, Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError as DjangoValidationError,
)
from django.db.models import ObjectDoesNotExist
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.serializers import ValidationError, as_serializer_error

from .scopes import Scope
from .utils import get_resource_for_path

if TYPE_CHECKING:
    from rest_framework.views import APIView  # noqa
    from rest_framework.viewsets import ViewSetMixin  # noqa

logger = logging.getLogger(__name__)


def get_required_scopes(
    request: Request, view: Union["APIView", "ViewSetMixin"]
) -> Union[Scope, None]:
    if not hasattr(view, "required_scopes"):
        raise ImproperlyConfigured(
            "The View(Set) must have a `required_scopes` attribute"
        )

    # viewsets mark detail routes by providing the initkwarg, see
    # rest_framework.routers.SimpleRouter.get_urls
    detail = getattr(view, "detail", False)
    action = getattr(view, "action", None)

    # auto-generated head method doesn't get an action assigned
    if action is None and detail and view.request.method == "HEAD":
        action = "retrieve"

    from rest_framework.viewsets import ViewSetMixin

    # if action is not set, fall back to the request method
    if action is None and not isinstance(view, ViewSetMixin):
        action = request.method.lower()

    scopes_required = view.required_scopes.get(action)
    return scopes_required


def bypass_permissions(request: Request) -> bool:
    """
    Bypass permission checks in DEBUG when using the browsable API renderer
    """
    return settings.DEBUG and isinstance(
        request.accepted_renderer, BrowsableAPIRenderer
    )


class AuthRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action
    and check that they are present in the AC for this client
    """

    permission_fields = ()
    main_resource = None

    def get_component(self, view) -> str:
        return view.queryset.model._meta.app_label

    def get_fields(self, data):
        if not isinstance(data, dict):
            raise exceptions.ParseError()
        return {field: data.get(field) for field in self.permission_fields}

    def format_data(self, obj, request) -> dict:
        main_resource = self.get_main_resource()
        serializer_class = main_resource.serializer_class
        serializer = serializer_class(obj, context={"request": request})
        return serializer.data

    def get_main_resource(self):
        if not self.main_resource:
            raise ImproperlyConfigured(
                "'%s' should either include a `main_resource` "
                "attribute, or override the `get_main_resource()` method."
                % self.__class__.__name__
            )
        return import_string(self.main_resource)

    def get_main_object(self, obj, permission_main_object):
        return getattr(obj, permission_main_object)

    def check_jwt_expiry(self, payload: Dict[str, Any]) -> None:
        """
        Verify that the token was issued recently enough.

        The Django settings define how long a JWT is considered to be valid. Adding
        that duration to the issued-at claim determines the upper limit for token
        validity.
        """
        if not payload:
            return

        iat = payload.get("iat")
        if iat is None:
            raise PermissionDenied(
                _("The JWT is mising the 'iat' claim."), code="jwt-missing-iat-claim"
            )

        current_timestamp = time.time()
        difference = current_timestamp - iat
        # check for "negative" clock drift
        if difference < 0 and difference < -settings.JWT_LEEWAY:
            logger.warning(
                "The JWT used for this request is not valid yet, the `iat` claim is "
                "newer than the current time stamp. You may want to check the clock drift "
                "on the Open Zaak server and/or tweak the `JWT_LEEWAY` setting.",
                extra={"payload": payload},
            )

        if difference >= (settings.JWT_EXPIRY + settings.JWT_LEEWAY):
            raise PermissionDenied(
                _("The JWT used for this request is expired"), code="jwt-expired"
            )

    def has_permission(self, request: Request, view) -> bool:
        # permission checks run before the handler is determined. if there is no handler,
        # a "method is not allowed" must be raised, not an HTTP 403 (see #385)
        # this implementation works for both APIView and viewsets
        has_handler = hasattr(view, request.method.lower())
        if not has_handler:
            view.http_method_not_allowed(request)

        # JWTs are only valid for a short amount of time
        self.check_jwt_expiry(request.jwt_auth.payload)

        from rest_framework.viewsets import ViewSetMixin

        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(request, view)
        component = self.get_component(view)

        if not self.permission_fields:
            return request.jwt_auth.has_auth(scopes_required, component)

        main_resource = self.get_main_resource()

        if view.action == "create":
            if view.__class__ is main_resource:
                main_object_data = request.data
                fields = self.get_fields(main_object_data)
                # validate fields, since it's a user input
                non_empty_fields = {
                    name: value for name, value in fields.items() if value
                }
                if non_empty_fields:
                    serializer = view.get_serializer(
                        data=non_empty_fields,
                        partial=True,
                        context={"request": request},
                    )
                    serializer.is_valid(raise_exception=True)

            else:
                main_object_url = request.data[view.permission_main_object]
                main_object_path = urlparse(main_object_url).path
                try:
                    main_object = get_resource_for_path(main_object_path)
                except ObjectDoesNotExist:
                    raise ValidationError(
                        {
                            view.permission_main_object: ValidationError(
                                _("The object does not exist in the database"),
                                code="object-does-not-exist",
                            ).detail
                        }
                    )
                except DjangoValidationError as exc:
                    err_dict = as_serializer_error(
                        ValidationError({view.permission_main_object: exc})
                    )
                    raise ValidationError(err_dict)

                main_object_data = self.format_data(main_object, request)
                fields = self.get_fields(main_object_data)

            return request.jwt_auth.has_auth(scopes_required, component, **fields)

        # detect if this is an unsupported method - if it's a viewset and the
        # action was not mapped, it's not supported and DRF will catch it
        if view.action is None and isinstance(view, ViewSetMixin):
            return True

        # by default - check if the action is allowed at all
        return request.jwt_auth.has_auth(scopes_required, component)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(request, view)
        component = self.get_component(view)

        if not self.permission_fields:
            return request.jwt_auth.has_auth(scopes_required, component)

        main_resource = self.get_main_resource()

        if view.__class__ is main_resource:
            main_object = obj
        else:
            main_object = self.get_main_object(obj, view.permission_main_object)

        main_object_data = self.format_data(main_object, request)
        fields = self.get_fields(main_object_data)
        return request.jwt_auth.has_auth(scopes_required, component, **fields)


class ClientIdRequired(permissions.BasePermission):
    """
    Look at the client_id of an object and check that it equals client_id in the JWT
    """

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            client_id = request.jwt_auth.client_id
            return client_id == obj.client_id


class BaseAuthRequired(permissions.BasePermission):
    """
    Perform a permission check based on required scopes.

    An :class:`APIView` or :class:`rest_framework.viewsets.ViewSet` needs to
    define the ``required_scopes`` attribute, mapping ``action`` to which
    scope is required. For :class:`APIView` you can specify which HTTP method
    they apply to. Viewset example:

        >>> class SomeViewSet(viewsets.ModelViewSet):
        ...     queryset = Some.objects.all()
        ...     permission_classes = (MainObjAuthRequired,)
        ...     required_scopes = {
        ...         "retrieve": Scope("some.scope"),
        ...         "list": Scope("some.scope"),
        ...         "create": Scope("some.scope"),
        ...         "update": Scope("some.scope"),
        ...         "partial_update": Scope("some.scope"),
        ...         "destroy": Scope("some.scope"),
        ...     }

    Or for APIView:

        >>> class SomeView(APIView):
        ...     permission_classes = (BaseAuthRequiredSubclass,)
        ...     required_scopes = {"get": Scope("some.scope")}
        ...
        ...     def get(self, request):
        ...         ...

    Note that you need a subclass setting :attr:`get_obj` or implementing
    :meth:`_get_object`.
    """

    permission_fields = ()
    get_obj = None
    obj_path = None

    def _get_obj(self, view, request):
        if not isinstance(self.get_obj, str):
            raise TypeError(
                "'get_obj' must be set to a string, representing a view method name"
            )

        method = getattr(view, self.get_obj)
        return method()

    def _get_obj_from_path(self, obj):
        if not isinstance(self.obj_path, str):
            raise TypeError(
                "'obj_path' must be a python dotted path to the main object FK"
            )

        bits = self.obj_path.split(".")
        for bit in bits:
            obj = getattr(obj, bit)
        return obj

    def _extract_field_value(self, main_obj, field):
        return getattr(main_obj, field)

    def _has_create_permission(
        self, request: Request, view: "APIView", scopes_required: Scope
    ) -> bool:
        try:
            main_obj = self._get_obj(view, request)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    # using self.obj_path here ASSUMES that the same serializer is used
                    # for input as output
                    self.obj_path: ValidationError(
                        _("The object does not exist in the database"),
                        code="object-does-not-exist",
                    ).detail
                }
            )
        fields = {
            k: self._extract_field_value(main_obj, k) for k in self.permission_fields
        }
        return request.jwt_auth.has_auth(scopes_required, **fields)

    def has_permission(self, request: Request, view) -> bool:
        from rest_framework.viewsets import ViewSetMixin

        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(request, view)

        if getattr(view, "action", None) == "create":
            return self._has_create_permission(request, view, scopes_required)

        # detect if this is an unsupported method - if it's a viewset and the
        # action was not mapped, it's not supported and DRF will catch it
        if isinstance(view, ViewSetMixin) and view.action is None:
            return True

        # by default - check if the action is allowed at all
        return request.jwt_auth.has_auth(scopes_required)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(request, view)
        main_obj = self._get_obj_from_path(obj)
        fields = {k: getattr(main_obj, k) for k in self.permission_fields}

        return request.jwt_auth.has_auth(scopes_required, **fields)


class MainObjAuthRequired(BaseAuthRequired):
    """
    Perform permission checks based on the main resource of the endpoint.
    """

    def _get_obj(self, view, request):
        return request.data

    def _get_obj_from_path(self, obj):
        return obj

    def _extract_field_value(self, main_obj, field):
        return main_obj.get(field, None)


class RelatedObjAuthRequired(BaseAuthRequired):
    """
    Perform permission checks based on an object related to the endpoint resource.
    """

    def _get_obj(self, view, request):
        main_obj_str = request.data.get(self.obj_path, None)
        main_obj_url = urlparse(main_obj_str).path
        main_obj = get_resource_for_path(main_obj_url)
        return main_obj


def permission_class_factory(base=BaseAuthRequired, **attrs) -> type:
    """
    Build a view-specific permission class

    This is just a small wrapper around ``type`` intended to keep the code readable.
    """
    name = base.__name__
    return type(name, (base,), attrs)
