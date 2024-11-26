import os

from vng_api_common.conf.api import *  # noqa


DEBUG = os.getenv("DEBUG", "no").lower() in ["yes", "true", "1"]

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "so-secret-i-cant-believe-you-are-looking-at-this"

ALLOWED_HOSTS = ["*"]

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "notifications_webhook",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_spectacular",
    "vng_api_common",
    "vng_api_common.notifications",
    "notifications_webhook",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "vng_api_common.middleware.AuthMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "notifications_webhook.urls"

# API settings
REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()

SPECTACULAR_SETTINGS = BASE_SPECTACULAR_SETTINGS.copy()
SPECTACULAR_SETTINGS.update(
    {
        "TITLE": "Notifications webhook receiver",
        "VERSION": "v1",
        "DESCRIPTION": "API Specification to be able to receive notifications from the NRC",
        "CONTACT": {"name": "VNG Realisatie", "url": "https://github.com/VNG-Realisatie/gemma-zaken"},
    }
)
