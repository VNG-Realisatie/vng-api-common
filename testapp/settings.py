import os

from vng_api_common.conf.api import *  # noqa
from vng_api_common.conf.api import JWT_SPECTACULAR_SETTINGS  # noqa

DEBUG = os.getenv("DEBUG", "no").lower() in ["yes", "true", "1"]

SITE_DOMAIN = os.getenv("SITE_DOMAIN", "example.com")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "so-secret-i-cant-believe-you-are-looking-at-this"

ALLOWED_HOSTS = ["*"]

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("PGDATABASE", "vng_api_common"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", 5432),
    }
}

# Geospatial libraries
GEOS_LIBRARY_PATH = None
GDAL_LIBRARY_PATH = None

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.messages",
    "rest_framework",
    "drf_spectacular",
    "simple_certmanager",
    "zgw_consumers",
    "notifications_api_common",
    "django_setup_configuration",
    "vng_api_common",
    "vng_api_common.authorizations",
    "vng_api_common.notifications",
    "vng_api_common.audittrails",
    "testapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "vng_api_common.authorizations.middleware.AuthMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

ROOT_URLCONF = "testapp.urls"

STATIC_URL = "/static/"

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()

SECURITY_DEFINITION_NAME = "JWT-Claims"

SPECTACULAR_SETTINGS = BASE_SPECTACULAR_SETTINGS.copy()
SPECTACULAR_SETTINGS.update(
    {
        "SECURITY_DEFINITIONS": {SECURITY_DEFINITION_NAME: {}},
        "TAGS": BASE_SPECTACULAR_SETTINGS.get("TAGS", [])
        + [
            {
                "name": "moloko_milk_bar",
                "description": "Global tag description via settings",
            },
        ],
        **JWT_SPECTACULAR_SETTINGS,
    }
)

IS_HTTPS = False
