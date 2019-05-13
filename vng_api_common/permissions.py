import warnings
from typing import Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from rest_framework import permissions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request

from .scopes import Scope
from .utils import get_resource_for_path


def get_required_scopes(view) -> Union[Scope, None]:
    if not hasattr(view, 'required_scopes'):
        raise ImproperlyConfigured("The View(Set) must have a `required_scopes` attribute")

    scopes_required = view.required_scopes.get(view.action)
    return scopes_required


def bypass_permissions(request: Request) -> bool:
    """
    Bypass permission checks in DBEUG when using the browsable API renderer
    """
    return settings.DEBUG and isinstance(request.accepted_renderer, BrowsableAPIRenderer)


class ActionScopesRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action and check that they
    are present in the JWT
    """

    def has_permission(self, request: Request, view) -> bool:
        if bypass_permissions(request):
            return True

        scopes_needed = get_required_scopes(view)
        # TODO: if no scopes are needed, what do???
        warnings.warn("The JWT-Payload based auth is deprecated, it will be "
                      "removed before July 22nd 2019", DeprecationWarning)
        return request.jwt_payload.has_scopes(scopes_needed)


class ScopesRequired(permissions.BasePermission):
    """
    Very simple scope-based permission, does not map to HTTP method or action.
    """

    def has_permission(self, request: Request, view) -> bool:
        # don't enforce them in the browsable API during debugging/development
        if bypass_permissions(request):
            return True

        if not hasattr(view, 'required_scopes'):
            raise ImproperlyConfigured("The View(Set) must have a `required_scopes` attribute")

        warnings.warn("The JWT-Payload based auth is deprecated, it will be "
                      "removed before July 22nd 2019", DeprecationWarning)
        return request.jwt_payload.has_scopes(view.required_scopes)


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
            warnings.warn("The JWT-Payload based auth is deprecated, it will be "
                          "removed before July 22nd 2019", DeprecationWarning)
            return request.jwt_payload['client_id'] == obj.client_id


class BaseAuthRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action
    and check that they are present in the AC for this client
    """
    permission_fields = ()
    get_obj = None
    obj_path = None

    def _get_obj(self, view, request):
        if not isinstance(self.get_obj, str):
            raise TypeError("'get_obj' must be set to a string, representing a view method name")

        method = getattr(view, self.get_obj)
        return method()

    def _get_obj_from_path(self, obj):
        if not isinstance(self.obj_path, str):
            raise TypeError("'obj_path' must be a python dotted path to the main object FK")

        bits = self.obj_path.split('.')
        for bit in bits:
            obj = getattr(obj, bit)
        return obj

    def _extract_field_value(self, main_obj, field):
        return getattr(main_obj, field)

    def has_permission(self, request: Request, view) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)

        if view.action == 'create':
            main_obj = self._get_obj(view, request)
            fields = {k: self._extract_field_value(main_obj, k) for k in self.permission_fields}
            return request.jwt_auth.has_auth(scopes_required, **fields)

        elif view.action == 'list':
            return request.jwt_auth.has_auth(scopes_required)

        return True

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)
        main_obj = self._get_obj_from_path(obj)
        fields = {k: getattr(main_obj, k) for k in self.permission_fields}

        return request.jwt_auth.has_auth(scopes_required, **fields)


class AuthScopesRequired(BaseAuthRequired):
    def _get_obj(self, view, request):
        return None

    def _get_obj_from_path(self, obj):
        return None


class MainObjAuthScopesRequired(BaseAuthRequired):
    def _get_obj(self, view, request):
        return request.data

    def _get_obj_from_path(self, obj):
        return obj

    def _extract_field_value(self, main_obj, field):
        return main_obj.get(field, None)


class RelatedObjAuthScopesRequired(BaseAuthRequired):
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
