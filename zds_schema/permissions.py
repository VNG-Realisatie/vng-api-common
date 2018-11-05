from typing import List

from django.core.exceptions import ImproperlyConfigured

from rest_framework import permissions
from rest_framework.request import Request


class ActionScopesRequired(permissions.BasePermission):
    """
    Look at the scopes required for the current action and check that they
    are present in the JWT
    """

    def get_required_scopes(self, view) -> List[str]:
        if not hasattr(view, 'required_scopes'):
            raise ImproperlyConfigured("The View(Set) must have a `required_scopes` attribute")

        scopes_required = view.required_scopes.get(view.action, [])
        return scopes_required

    def has_permission(self, request: Request, view) -> bool:
        scopes_needed = self.get_required_scopes(view)
        # TODO: if no scopes are needed, what do???
        return request.jwt_payload.has_scopes(scopes_needed)
