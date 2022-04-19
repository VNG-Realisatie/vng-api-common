from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve

from .models import Group, Hobby, Person
from .serializers import GroupSerializer, HobbySerializer, PersonSerializer


@conditional_retrieve(extra_depends_on={"group"})
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Title

    Summary

    More summary

    retrieve:
    Some description
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@conditional_retrieve()
class HobbyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
