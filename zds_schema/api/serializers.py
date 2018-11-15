from rest_framework import serializers

from ..models import JWTSecret


class JWTSecretSerializer(serializers.ModelSerializer):
    class Meta:
        model = JWTSecret
        fields = ('identifier', 'secret')
