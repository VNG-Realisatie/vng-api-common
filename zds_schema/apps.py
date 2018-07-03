from django.apps import AppConfig

from drf_yasg import openapi
from drf_yasg.inspectors.field import basic_type_info


class ZDSSchemaConfig(AppConfig):
    name = 'zds_schema'

    def ready(self):
        register_geo_type()


def register_geo_type():
    try:
        from rest_framework_gis.fields import GeometryField
    except ImportError:
        pass
    else:
        basic_type_info.append(
            (GeometryField, (openapi.TYPE_OBJECT, None))
        )
