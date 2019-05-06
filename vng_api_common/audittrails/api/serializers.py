from rest_framework import serializers

from ..models import AuditTrail


class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = (
            'uuid',
            'bron',
            # 'applicatieId',
            # 'applicatieWeergave',
            # 'gebruikersId',
            # 'gebruikersWeergave',
            'actie',
            'actieWeergave',
            'resultaat',
            'hoofdObject',
            'resource',
            'resourceUrl',
            # 'resourceWeergave',
            # 'toelichting',
            'aanmaakdatum',
            'wijzigingen',
        )
