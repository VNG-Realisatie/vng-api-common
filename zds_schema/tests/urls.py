from django.conf import settings
from django.urls import reverse as _reverse, reverse_lazy as _reverse_lazy


def reverse(*args, **kwargs):
    kwargs.setdefault('kwargs', {})
    kwargs['kwargs']['version'] = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    return _reverse(*args, **kwargs)


def reverse_lazy(*args, **kwargs):
    kwargs.setdefault('kwargs', {})
    kwargs['kwargs']['version'] = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    return _reverse_lazy(*args, **kwargs)
