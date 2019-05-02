from typing import Any

from django.db.models.base import ModelBase
from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema


def action_description(action: str, description: str):
    decorator = swagger_auto_schema(operation_description=description)
    return method_decorator(name=action, decorator=decorator)


def field_default(field: str, default: Any):

    def decorator(cls: ModelBase):
        model_field = cls._meta.get_field(field)
        model_field.default = default
        return cls

    return decorator
