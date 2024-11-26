__all__ = [
    "API_VERSION",
    "BASE_REST_FRAMEWORK",
    "BASE_SPECTACULAR_SETTINGS",
    "COMMON_SPEC",
    "LINK_FETCHER",
    "GEMMA_URL_TEMPLATE",
    "GEMMA_URL_COMPONENTTYPE",
    "GEMMA_URL_INFORMATIEMODEL",
    "GEMMA_URL_INFORMATIEMODEL_VERSIE",
    "REDOC_SETTINGS",
    "NOTIFICATIONS_KANAAL",
    "NOTIFICATIONS_DISABLED",
    "JWT_LEEWAY",
    "SECURITY_DEFINITION_NAME",
    "COMMONGROUND_API_COMMON_GET_DOMAIN",
    "JWT_SPECTACULAR_SETTINGS",
]

API_VERSION = "1.0.0-rc1"  # semantic version

SECURITY_DEFINITION_NAME = "JWT-Claims"

BASE_REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "vng_api_common.schema.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    # there is no authentication of 'end-users', only authorization (via JWT)
    # of applications
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_FILTER_BACKENDS": ("vng_api_common.filters.Backend",),
    #
    # # Filtering
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
BASE_SPECTACULAR_SETTINGS = {
    "DEFAULT_GENERATOR_CLASS": "vng_api_common.generators.OpenAPISchemaGenerator",
    "SERVE_INCLUDE_SCHEMA": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# add to SPECTACULAR_SETTINGS if you are using the AuthMiddleware
JWT_SPECTACULAR_SETTINGS = {
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            SECURITY_DEFINITION_NAME: {
                "type": "http",
                "bearerFormat": "JWT",
                "scheme": "bearer",
            }
        },
    },
    "SECURITY": [
        {
            SECURITY_DEFINITION_NAME: [],
        }
    ],
}


REDOC_SETTINGS = {"EXPAND_RESPONSES": "200,201", "SPEC_URL": "openapi.json"}

# See: https://github.com/Rebilly/ReDoc#redoc-options-object
LINK_FETCHER = "requests.get"

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
