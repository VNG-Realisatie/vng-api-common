import logging

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from vng_api_common.authorizations.models import Applicatie, Autorisatie

logger = logging.getLogger(__name__)


class AutorisatieSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Autorisatie
        fields = (
            'component',
            'scopes',
            'zaaktype',
            'max_vertrouwelijkheidaanduiding',
        )


class ApplicatieSerializer(serializers.HyperlinkedModelSerializer):
    autorisaties = AutorisatieSerializer(many=True, required=False)

    class Meta:
        model = Applicatie
        fields = (
            'url',
            'client_ids',
            'label',
            'heeft_alle_autorisaties',
            'autorisaties'
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'uuid',
            },
            'heeft_alle_autorisaties': {
                'required': False,
            }

        }

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)

        # either autorisaties or heeft_alle_autorisaties can be specified
        autorisaties_obj = None
        heeft_alle_autorisaties_obj = None
        # in case of update:
        if self.instance:
            autorisaties_obj = self.instance.autorisaties.all()
            heeft_alle_autorisaties_obj = self.instance.heeft_alle_autorisaties

        autorisaties = validated_attrs.get('autorisaties', None) or autorisaties_obj
        heeft_alle_autorisaties = validated_attrs.get('heeft_alle_autorisaties', None) or heeft_alle_autorisaties_obj

        if autorisaties and heeft_alle_autorisaties is True:
            raise serializers.ValidationError(
                _('Either autorisaties or heeft_alle_autorisaties can be specified'),
                code='ambiguous-authorizations-specified')

        if not autorisaties and heeft_alle_autorisaties is not True:
            raise serializers.ValidationError(
                _('Either autorisaties or heeft_alle_autorisaties should be specified'),
                code='missing-authorizations')

        return validated_attrs

    @transaction.atomic
    def create(self, validated_data):
        autorisaties_data = validated_data.pop('autorisaties', None)
        applicatie = super().create(validated_data)

        if autorisaties_data:
            for auth in autorisaties_data:
                Autorisatie.objects.create(**auth, applicatie=applicatie)

        return applicatie

    @transaction.atomic
    def update(self, instance, validated_data):
        autorisaties_data = validated_data.pop('autorisaties', None)
        applicatie = super().update(instance, validated_data)

        # in case of update autorisaties - remove all related autorisaties
        if autorisaties_data:
            applicatie.autorisaties.all().delete()
            for auth in autorisaties_data:
                Autorisatie.objects.create(**auth, applicatie=applicatie)

        return applicatie
