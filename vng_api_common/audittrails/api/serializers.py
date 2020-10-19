from rest_framework import serializers

from ...constants import CommonResourceAction, ComponentTypes
from ...serializers import GegevensGroepSerializer, add_choice_values_help_text
from ..models import AuditTrail


class WijzigingenSerializer(GegevensGroepSerializer):
    class Meta:
        model = AuditTrail
        gegevensgroep = "wijzigingen"


class AuditTrailSerializer(serializers.ModelSerializer):
    wijzigingen = WijzigingenSerializer()

    class Meta:
        model = AuditTrail
        fields = (
            "uuid",
            "bron",
            "applicatie_id",
            "applicatie_weergave",
            "gebruikers_id",
            "gebruikers_weergave",
            "actie",
            "actie_weergave",
            "resultaat",
            "hoofd_object",
            "resource",
            "resource_url",
            "toelichting",
            "resource_weergave",
            "aanmaakdatum",
            "wijzigingen",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        value_display_mapping = add_choice_values_help_text(ComponentTypes)
        self.fields["bron"].help_text += f"\n\n{value_display_mapping}"

        # Indicate that the values for AuditTrail.actie are not limited to
        # the CommonResourceActions
        custom_msg = """De bekende waardes voor dit veld zijn hieronder aangegeven, \
                        maar andere waardes zijn ook toegestaan"""

        value_display_mapping = add_choice_values_help_text(CommonResourceAction)
        self.fields["actie"].help_text += f"\n\n{custom_msg}\n\n{value_display_mapping}"
