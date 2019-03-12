from typing import Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from rest_framework import permissions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request

from .scopes import Scope


class ActionScopesRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action and check that they
    are present in the JWT
    """

    def get_required_scopes(self, view) -> Union[Scope, None]:
        if not hasattr(view, 'required_scopes'):
            raise ImproperlyConfigured("The View(Set) must have a `required_scopes` attribute")

        scopes_required = view.required_scopes.get(view.action)
        return scopes_required

    def has_permission(self, request: Request, view) -> bool:
        if settings.DEBUG and isinstance(request.accepted_renderer, BrowsableAPIRenderer):
            return True

        scopes_needed = self.get_required_scopes(view)
        # TODO: if no scopes are needed, what do???
        return request.jwt_payload.has_scopes(scopes_needed)


class ScopesRequired(permissions.BasePermission):
    """
    Very simple scope-based permission, does not map to HTTP method or action.
    """

    def has_permission(self, request: Request, view) -> bool:
        # don't enforce them in the browsable API during debugging/development
        if settings.DEBUG and isinstance(request.accepted_renderer, BrowsableAPIRenderer):
            return True

        if not hasattr(view, 'required_scopes'):
            raise ImproperlyConfigured("The View(Set) must have a `required_scopes` attribute")

        return request.jwt_payload.has_scopes(view.required_scopes)
