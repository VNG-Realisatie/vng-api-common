"""
Provide notifications kanaal/exchange classes.
"""
from typing import Dict, List, Tuple

from django.core.exceptions import ImproperlyConfigured
from django.db.models import FieldDoesNotExist, Model
from django.db.models.base import ModelBase

KANAAL_REGISTRY = set()


class Kanaal:

    def __init__(self, label: str, main_resource: ModelBase, kenmerken: Tuple = None):
        self.label = label
        self.main_resource = main_resource

        # check that we're refering to existing fields
        self.kenmerken = kenmerken or ()
        for kenmerk in self.kenmerken:
            try:
                self.main_resource._meta.get_field(kenmerk)
            except FieldDoesNotExist as exc:
                raise ImproperlyConfigured(
                    f"Kenmerk '{kenmerk}' does not exist on the model {main_resource}"
                ) from exc

        KANAAL_REGISTRY.add(self)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "%s(label=%r, main_resource=%r)" % (cls_name, self.label, self.main_resource)

    def get_kenmerken(self, obj: Model) -> List[Dict]:
        kenmerken = []
        for kenmerk in self.kenmerken:
            kenmerken.append({kenmerk: getattr(obj, kenmerk)})
        return kenmerken
