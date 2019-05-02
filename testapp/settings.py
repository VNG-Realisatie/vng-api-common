import os

from vng_api_common.conf.api import *  # noqa

DEBUG = os.getenv('DEBUG', 'no').lower() in ['yes', 'true', '1']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'so-secret-i-cant-believe-you-are-looking-at-this'

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vng_api_common',
        'USER': 'vng_api_common',
        'PASSWORD': 'vng_api_common',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'rest_framework',
    'drf_yasg',

    'vng_api_common',
    'vng_api_common.authorizations',
    'vng_api_common.notifications',

    'testapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'testapp.urls'

STATIC_URL = '/static/'

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()

SWAGGER_SETTINGS = BASE_SWAGGER_SETTINGS.copy()

SWAGGER_SETTINGS['DEFAULT_FIELD_INSPECTORS'] = SWAGGER_SETTINGS['DEFAULT_FIELD_INSPECTORS'][1:]

SWAGGER_SETTINGS.update({
    'DEFAULT_INFO': 'testapp.schema.info',
    'SECURITY_DEFINITIONS': {},
})
