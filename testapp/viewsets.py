from rest_framework import viewsets

from .models import Person
from .serializers import PersonSerializer


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
