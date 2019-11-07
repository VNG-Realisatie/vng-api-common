from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.views import APIView

from ..constants import ComponentTypes
from ..permissions import BaseAuthRequired, bypass_permissions, get_required_scopes


class JWTCreatePermission(BaseAuthRequired):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if bypass_permissions(request):
            return True

        if not isinstance(view, CreateAPIView):
            return False

        if not hasattr(view, "action"):
            view.action = "create"

        scopes_required = get_required_scopes(view)
        return request.jwt_auth.has_auth(scopes_required, component=ComponentTypes.ac)
