from pkg_resources import get_distribution

__version__ = get_distribution('vng-api-common').version

default_app_config = 'vng_api_common.apps.ZDSSchemaConfig'
