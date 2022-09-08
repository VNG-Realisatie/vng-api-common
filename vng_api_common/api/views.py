from rest_framework.generics import CreateAPIView

from ..models import JWTSecret
from ..scopes import Scope
from .permissions import JWTCreatePermission
from .serializers import JWTSecretSerializer


class CreateJWTSecretView(CreateAPIView):
    schema = None

    model = JWTSecret
    serializer_class = JWTSecretSerializer
    permission_classes = (JWTCreatePermission,)
    required_scopes = {
        "create": Scope("autorisaties.credentials-registreren", private=True)
    }
