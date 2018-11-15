from rest_framework.generics import CreateAPIView

from ..models import JWTSecret
from .serializers import JWTSecretSerializer


class CreateJWTSecretView(CreateAPIView):
    swagger_schema = None

    model = JWTSecret
    serializer_class = JWTSecretSerializer
    permission_classes = ()  # TODO: protect with auth as well
