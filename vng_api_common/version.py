from django.conf import settings


def get_major_version() -> str:
    bits = settings.API_VERSION.split(".")
    return bits[0]
