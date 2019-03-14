from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class NotificatieSerializer(serializers.Serializer):
    kanaal = serializers.CharField(label=_("kanaal"))
    hoofd_object = serializers.URLField(label=_("URL naar het hoofdobject"))
    resource = serializers.CharField(label=_("resource"))
    resource_url = serializers.URLField(label=_("URL naar de resource waarover de notificatie gaat"))
    actie = serializers.CharField(label=_("actie"))
    aanmaakdatum = serializers.DateTimeField(label=_("aanmaakdatum"))
    kenmerken = serializers.JSONField(label=_("kenmerken"), required=False)
