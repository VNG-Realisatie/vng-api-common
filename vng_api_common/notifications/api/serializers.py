from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from ...validators import UntilNowValidator


class NotificatieSerializer(serializers.Serializer):
    kanaal = serializers.CharField(
        label=_("kanaal"),
        max_length=50,
        help_text=_(
            "De naam van het kanaal (`KANAAL.naam`) waar het bericht "
            "op moet worden gepubliceerd."
        ),
    )
    hoofd_object = serializers.URLField(
        label=_("hoofd object"),
        help_text=_(
            "URL-referentie naar het hoofd object van de publicerende "
            "API die betrekking heeft op de `resource`."
        ),
    )
    resource = serializers.CharField(
        label=_("resource"),
        max_length=100,
        help_text=_("De resourcenaam waar de notificatie over gaat."),
    )
    resource_url = serializers.URLField(
        label=_("resource URL"),
        help_text=_("URL-referentie naar de `resource` van de publicerende " "API."),
    )
    actie = serializers.CharField(
        label=_("actie"),
        max_length=100,
        help_text=_(
            "De actie die door de publicerende API is gedaan. De "
            "publicerende API specificeert de toegestane acties."
        ),
    )
    aanmaakdatum = serializers.DateTimeField(
        label=_("aanmaakdatum"),
        validators=[UntilNowValidator()],
        help_text=_("Datum en tijd waarop de actie heeft plaatsgevonden."),
    )
    kenmerken = serializers.DictField(
        label=_("kenmerken"),
        required=False,
        child=serializers.CharField(
            label=_("kenmerk"),
            max_length=1000,
            help_text=_("Een waarde behorende bij de sleutel."),
        ),
        help_text=_(
            "Mapping van kenmerken (sleutel/waarde) van de notificatie. De "
            "publicerende API specificeert de toegestane kenmerken."
        ),
    )
