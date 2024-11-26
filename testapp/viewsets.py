from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from vng_api_common.caching import conditional_retrieve
from vng_api_common.geo import GeoMixin
from vng_api_common.pagination import DynamicPageSizePagination

from .models import GeometryModel, Group, Hobby, MediaFileModel, Person, Poly
from .serializers import (
    GeometryModelSerializer,
    GroupSerializer,
    HobbySerializer,
    MediaFileModelSerializer,
    PersonSerializer,
    PolySerializer,
)


@extend_schema_view(
    list=extend_schema(
        description="Summary\n\nMore summary",
    ),
    retrieve=extend_schema(description="Some description"),
)
@conditional_retrieve(extra_depends_on={"group"})
class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@conditional_retrieve()
class HobbyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class PaginateHobbyViewSet(viewsets.ModelViewSet):
    queryset = Hobby.objects.all().order_by("id")
    serializer_class = HobbySerializer
    pagination_class = DynamicPageSizePagination


class PolyViewSet(viewsets.ModelViewSet):
    queryset = Poly.objects.all()
    serializer_class = PolySerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFileModel.objects.all()
    serializer_class = MediaFileModelSerializer


class GeometryViewSet(GeoMixin, viewsets.ModelViewSet):
    queryset = GeometryModel.objects.all()
    serializer_class = GeometryModelSerializer
