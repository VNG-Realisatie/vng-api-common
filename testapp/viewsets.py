from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve

from .models import Group, Hobby, Person
from .serializers import GroupSerializer, HobbySerializer, PersonSerializer


@extend_schema_view(retrieve=extend_schema(description="Some description"))
@conditional_retrieve(extra_depends_on={"group"})
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    global_description = _("This is the global resource description")


@conditional_retrieve()
class HobbyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
