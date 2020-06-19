from typing import Optional, Type

from django.db import models

from rest_framework.utils.model_meta import get_field_info


def get_target_field(model: Type[models.Model], field: str) -> Optional[models.Field]:
    """
    Retrieve the end-target that ``field`` points to.

    :param field: A string containing a lookup, potentially spanning relations. E.g.:
      foo__bar__lte.
    :return: A Django model field instance or `None`
    """

    start, *remaining = field.split("__")
    field_info = get_field_info(model)

    # simple, non relational field?
    if start in field_info.fields:
        return field_info.fields[start]

    # simple relational field?
    if start in field_info.forward_relations:
        relation_info = field_info.forward_relations[start]
        if not remaining:
            return relation_info.model_field
        else:
            return get_target_field(relation_info.related_model, "__".join(remaining))

    # check the reverse relations - note that the model name is used instead of model_name_set
    # in the queries -> we can't just test for containment in field_info.reverse_relations
    for relation_info in field_info.reverse_relations.values():
        # not sure about this - what if there are more relations with different related names?
        if relation_info.related_model._meta.model_name != start:
            continue
        return get_target_field(relation_info.related_model, "__".join(remaining))

    return None
