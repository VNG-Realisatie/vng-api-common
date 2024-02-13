from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve
from vng_api_common.pagination import DynamicPageSizePagination

from .models import Group, Hobby, Person
from .serializers import GroupSerializer, HobbySerializer, PersonSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Title",
        description="Summary\n\nMore summary",
    ),
    retrieve=extend_schema(description="Some description"),
)
@conditional_retrieve(extra_depends_on={"group"})
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

    # def __getattribute__(self, name):
    #     if name == "action_map":
    #         breakpoint()
    #     return super().__getattibute__(name)
    #
    # def __setattr__(self, name, value):
    #     if name == "action_map":
    #         breakpoint()
    #     return super().__setattr__(name, value)


@conditional_retrieve()
class HobbyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class PaginateHobbyViewSet(viewsets.ModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer
    pagination_class = DynamicPageSizePagination
