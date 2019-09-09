from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve

from .models import Hobby, Person
from .serializers import HobbySerializer, PersonSerializer


@conditional_retrieve()
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@conditional_retrieve()
class HobbyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer
