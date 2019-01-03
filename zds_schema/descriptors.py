from typing import Dict

from django.db import models


class GegevensGroepType:
    """
    Structure a body of data from flat model fields.

    All keys are always truthy for a value.

    :param mapping: dict, mapping simple keys to model fields
    """
    name = None
    model = None

    def __init__(self, mapping: Dict[str, models.Field]):
        self.mapping = mapping

    def __get__(self, obj, type=None):
        if obj is None:  # accessed through the owner, i.e. the model -> introspection
            return self

        return {
            key: getattr(obj, field.name)
            for key, field in self.mapping.items()
        }

    def __set__(self, obj, value: dict):
        # value can be empty, if that's the case, empty all model fields
        if not value:
            for field in self.mapping.values():
                empty_value = None if field.null else ''
                setattr(obj, field.name, empty_value)
            return

        # map the values
        for key, field in self.mapping.items():
            setattr(obj, field.name, value[key])
            assert getattr(obj, field.name, None), f"Empty '{key}' not allowed"
