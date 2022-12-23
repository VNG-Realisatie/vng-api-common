__all__ = [
    "API_VERSION",
    "BASE_REST_FRAMEWORK",
    "BASE_SWAGGER_SETTINGS",
    "COMMON_SPEC",
    "LINK_FETCHER",
    "ZDS_CLIENT_CLASS",
    "GEMMA_URL_TEMPLATE",
    "GEMMA_URL_COMPONENTTYPE",
    "GEMMA_URL_INFORMATIEMODEL",
    "GEMMA_URL_INFORMATIEMODEL_VERSIE",
    "REDOC_SETTINGS",
    "NOTIFICATIONS_KANAAL",
    "NOTIFICATIONS_DISABLED",
    "JWT_LEEWAY",
]

API_VERSION = "1.0.0-rc1"  # semantic version

BASE_REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # 'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        # 'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication'
    ),
    # there is no authentication of 'end-users', only authorization (via JWT)
    # of applications
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'oauth2_provider.contrib.rest_framework.TokenHasReadWriteScope',
    #     # 'rest_framework.permissions.IsAuthenticated',
    #     # 'rest_framework.permissions.AllowAny',
    # ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    #
    # # Generic view behavior
    # 'DEFAULT_PAGINATION_CLASS': 'ztc.api.utils.pagination.HALPagination',
    "DEFAULT_FILTER_BACKENDS": (
        "vng_api_common.filters.Backend",
        # 'rest_framework.filters.SearchFilter',
        # 'rest_framework.filters.OrderingFilter',
    ),
    #
    # # Filtering
    # 'SEARCH_PARAM': 'zoek',  # 'search',
    "ORDERING_PARAM": "ordering",  # 'ordering',
    #
    # Versioning
    "DEFAULT_VERSION": "1",  # NOT to be confused with API_VERSION - it's the major version part
    "ALLOWED_VERSIONS": ("1",),
    "VERSION_PARAM": "version",
    #
    # # Exception handling
    "EXCEPTION_HANDLER": "vng_api_common.views.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

BASE_SWAGGER_SETTINGS = {
    "DEFAULT_GENERATOR_CLASS": "vng_api_common.generators.OpenAPISchemaGenerator",
    "DEFAULT_AUTO_SCHEMA_CLASS": "vng_api_common.inspectors.view.AutoSchema",
    "DEFAULT_INFO": "must.be.overridden",
    "DEFAULT_FIELD_INSPECTORS": (
        # GeometryFieldInspector has external dependencies, and is opt-in
        # 'vng_api_common.inspectors.geojson.GeometryFieldInspector',
        "vng_api_common.inspectors.fields.HyperlinkedIdentityFieldInspector",
        "vng_api_common.inspectors.fields.ReadOnlyFieldInspector",
        "vng_api_common.inspectors.polymorphic.PolymorphicSerializerInspector",
        "vng_api_common.inspectors.fields.GegevensGroepInspector",
        "drf_yasg.inspectors.CamelCaseJSONFilter",
        "drf_yasg.inspectors.RecursiveFieldInspector",
        "drf_yasg.inspectors.ReferencingSerializerInspector",
        "drf_yasg.inspectors.ChoiceFieldInspector",
        "drf_yasg.inspectors.FileFieldInspector",
        "drf_yasg.inspectors.DictFieldInspector",
        "drf_yasg.inspectors.JSONFieldInspector",
        "drf_yasg.inspectors.HiddenFieldInspector",
        "drf_yasg.inspectors.RelatedFieldInspector",
        "drf_yasg.inspectors.SerializerMethodFieldInspector",
        "drf_yasg.inspectors.SimpleFieldInspector",
        "drf_yasg.inspectors.StringDefaultFieldInspector",
    ),
    "DEFAULT_FILTER_INSPECTORS": ("vng_api_common.inspectors.query.FilterInspector",),
}

REDOC_SETTINGS = {"EXPAND_RESPONSES": "200,201", "SPEC_URL": "openapi.json"}

# See: https://github.com/Rebilly/ReDoc#redoc-options-object
LINK_FETCHER = "requests.get"

ZDS_CLIENT_CLASS = "zds_client.Client"

GEMMA_URL_TEMPLATE = "https://www.gemmaonline.nl/index.php/{informatiemodel}_{versie}/doc/{componenttype}/{component}"
GEMMA_URL_COMPONENTTYPE = "objecttype"
GEMMA_URL_INFORMATIEMODEL = "Rgbz"
GEMMA_URL_INFORMATIEMODEL_VERSIE = "2.0"

# notifications configuration

NOTIFICATIONS_KANAAL = None
NOTIFICATIONS_DISABLED = False

vng_repo = "VNG-Realisatie/vng-api-common"
vng_branch = "ref-responses"
COMMON_SPEC = f"https://raw.githubusercontent.com/{vng_repo}/feature/{vng_branch}/vng_api_common/schemas/common.yaml"

JWT_LEEWAY = 0  # default in PyJWT

COMMONGROUND_API_COMMON_GET_DOMAIN = "vng_api_common.utils.get_site_domain"
