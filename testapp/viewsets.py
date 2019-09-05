from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve

from .models import Person
from .serializers import PersonSerializer


@conditional_retrieve()
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
