from typing import Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.serializers import ValidationError

from .scopes import Scope
from .utils import get_resource_for_path


def get_required_scopes(view) -> Union[Scope, None]:
    if not hasattr(view, "required_scopes"):
        raise ImproperlyConfigured(
            "The View(Set) must have a `required_scopes` attribute"
        )

    scopes_required = view.required_scopes.get(view.action)
    return scopes_required


def bypass_permissions(request: Request) -> bool:
    """
    Bypass permission checks in DBEUG when using the browsable API renderer
    """
    return settings.DEBUG and isinstance(
        request.accepted_renderer, BrowsableAPIRenderer
    )


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
    Look at the scopes required for the current action
    and check that they are present in the AC for this client
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

    def has_permission(self, request: Request, view) -> bool:
        from rest_framework.viewsets import ViewSetMixin

        if bypass_permissions(request):
            return True

        scopes_required = get_required_scopes(view)

        if view.action == "create":
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
                k: self._extract_field_value(main_obj, k)
                for k in self.permission_fields
            }
            return request.jwt_auth.has_auth(scopes_required, **fields)

        # detect if this is an unsupported method - if it's a viewset and the
        # action was not mapped, it's not supported and DRF will catch it
        if isinstance(view, ViewSetMixin) and view.action is None:
            return True

        # by default - check if the action is allowed at all
        return request.jwt_auth.has_auth(scopes_required)

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
