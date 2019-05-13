from rest_framework import serializers

from ..models import AuditTrail


class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = (
            'uuid',
            'bron',
            # 'applicatie_id',
            # 'applicatie_weergave',
            # 'gebruikers_id',
            # 'gebruikers_weergave',
            'actie',
            'actie_weergave',
            'resultaat',
            'hoofd_object',
            'resource',
            'resource_url',
            # 'resource_weergave',
            # 'toelichting',
            'aanmaakdatum',
            'wijzigingen',
        )
