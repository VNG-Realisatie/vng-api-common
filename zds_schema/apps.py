from django.apps import AppConfig

from drf_yasg import openapi
from drf_yasg.inspectors.field import basic_type_info
from rest_framework_gis.fields import GeometryField


class ZDSSchemaConfig(AppConfig):
    name = 'zds_schema'

    def ready(self):
        register_geo_type()


def register_geo_type():
    basic_type_info.append(
        (GeometryField, (openapi.TYPE_OBJECT, None))
    )
