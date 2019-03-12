import inspect

from django.conf import settings
from django.db import models
from django.urls import reverse as _reverse, reverse_lazy as _reverse_lazy


def _magic_args(args, kwargs):
    """
    Do some trivial introspection to translate objects/models into common
    used urls.
    """
    if args and isinstance(args[0], models.Model):
        url_name = f"{args[0]._meta.model_name}-detail"
        kwargs['kwargs'].setdefault('uuid', args[0].uuid)
        args = (url_name,) + args[1:]
    elif args and inspect.isclass(args[0]) and issubclass(args[0], models.Model):
        url_name = f"{args[0]._meta.model_name}-list"
        args = (url_name,) + args[1:]
    return args, kwargs


def reverse(*args, **kwargs):
    kwargs.setdefault('kwargs', {})
    kwargs['kwargs']['version'] = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    args, kwargs = _magic_args(args, kwargs)
    return _reverse(*args, **kwargs)


def reverse_lazy(*args, **kwargs):
    kwargs.setdefault('kwargs', {})
    kwargs['kwargs']['version'] = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    args, kwargs = _magic_args(args, kwargs)
    return _reverse_lazy(*args, **kwargs)
