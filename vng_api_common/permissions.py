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


class AuthScopesRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action
    and check that they are present in the AC for this client
    """
    permission_fields = None

    def get_permission_fields(self):
        return self.permission_fields or {}

    def get_from_request_default(self, request, field):
        return None

    def get_from_object_default(self, obj, field):
        return None

    def has_permission(self, request: Request, view) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)

        if view.action == 'create':
            fields_from_request = {}
            for field in self.get_permission_fields():
                if hasattr(self, f'get_{field}_from_request'):
                    fields_from_request[field] = getattr(self, f'get_{field}_from_request')(request)
                else:
                    fields_from_request[field] = self.get_from_request_default(request, field)

            return request.jwt_auth.has_auth(scopes_required, **fields_from_request)

        elif view.action == 'list':
            return request.jwt_auth.has_auth(scopes_required)

        return True

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)

        fields_from_object = {}
        for field in self.get_permission_fields():
            if hasattr(self, f'get_{field}'):
                fields_from_object[field] = getattr(self, f'get_{field}')(obj)
            else:
                fields_from_object[field] = self.get_from_object_default(obj, field)

        return request.jwt_auth.has_auth(scopes_required, **fields_from_object)


class MainObjAuthScopesRequired(AuthScopesRequired):
    def get_from_request_default(self, request, field):
        return request.data.get(field, None)

    def get_from_object_default(self, obj, field):
        return getattr(obj, field)


class RelatedObjAuthScopesRequired(AuthScopesRequired):
    main_object = None

    def get_from_request_default(self, request, field):
        main_obj_str = request.data.get(self.main_object, None)
        main_obj_url = urlparse(main_obj_str).path
        main_obj = get_resource_for_path(main_obj_url)
        return getattr(main_obj, field)

    def get_from_object_default(self, obj, field):
        main_obj = getattr(obj, self.main_object)
        return getattr(main_obj, field)
