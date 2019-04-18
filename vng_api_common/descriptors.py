from typing import Dict

from django.db import models


class GegevensGroepType:
    """
    Structure a body of data from flat model fields.

    All keys are always truthy for a value.

    :param mapping: dict, mapping simple keys to model fields
    :param optional: iterable of fields that are NOT required.
    :param none_for_empty: convert 'empty' values to None, such as empty
      strings. Booleans are left untouched
    """
    name = None
    model = None

    def __init__(self, mapping: Dict[str, models.Field], optional: tuple=None, none_for_empty=False):
        self.mapping = mapping
        self.optional = optional or ()
        self.none_for_empty = none_for_empty

        all_fields_known = set(self.optional).issubset(set(mapping.keys()))
        assert all_fields_known, "The fields in 'optional' must be a subset of the mapping keys"

        # check if it's optional or not
        self.required = any(field.blank is False for field in self.mapping.values())

    def __repr__(self):
        fields = ", ".join([
            field if field not in self.optional else f"{field} (optional)"
            for field in self.mapping.keys()
        ])
        return "<GegevensGroepType: fields=%r required=%r>" % (fields, self.required)

    def __get__(self, obj, type=None):
        if obj is None:  # accessed through the owner, i.e. the model -> introspection
            return self

        def _value_getter(attr):
            val = getattr(obj, attr)
            if not self.none_for_empty:
                return val

            if isinstance(val, bool):
                return val

            # 'empty'-ish value check
            if not val:
                return None

            return val

        return {
            key: _value_getter(field.name)
            for key, field in self.mapping.items()
        }

    def __set__(self, obj, value: dict):
        # value can be empty, if that's the case, empty all model fields
        if not value:
            if self.required:
                raise ValueError("A non-empty value is required")

            for field in self.mapping.values():
                empty_value = None if field.null else ''
                default_value = field.default if field.default != models.NOT_PROVIDED else empty_value
                setattr(obj, field.name, default_value)
            return

        # map the values
        for key, field in self.mapping.items():
            setattr(obj, field.name, value[key])

            if key not in self.optional:
                attr_value = getattr(obj, field.name, None)
                assert attr_value is not None, f"Empty '{key}' not allowed"
