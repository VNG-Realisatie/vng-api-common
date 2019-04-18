from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class NotificatieSerializer(serializers.Serializer):
    kanaal = serializers.CharField(label=_("kanaal"), max_length=50)
    hoofd_object = serializers.URLField(label=_("URL naar het hoofdobject"))
    resource = serializers.CharField(label=_("resource"), max_length=100)
    resource_url = serializers.URLField(label=_("URL naar de resource waarover de notificatie gaat"))
    actie = serializers.CharField(label=_("actie"), max_length=100)
    aanmaakdatum = serializers.DateTimeField(label=_("aanmaakdatum"))
    kenmerken = serializers.DictField(
        child=serializers.CharField(max_length=1000),
        required=False
    )
