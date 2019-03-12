from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema


def action_description(action: str, description: str):
    decorator = swagger_auto_schema(operation_description=description)
    return method_decorator(name=action, decorator=decorator)
