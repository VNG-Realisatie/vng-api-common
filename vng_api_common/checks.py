import re
from typing import Any

from django.core.checks import Warning, register

from djchoices import DjangoChoices

from .utils import get_subclasses

ENUM_VALUE_PATTERN = re.compile(r"^[a-z_0-9]+$", re.ASCII)


def enum_value_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return True

    match = ENUM_VALUE_PATTERN.match(value)
    if not match:
        return False

    return True


@register()
def check_lowercased_constants(app_configs, **kwargs):
    """
    Check that enum values have lowercased, underscore only values.
    """
    warnings = []

    for klass in get_subclasses(DjangoChoices):
        enum_values = klass.values.keys()
        if any((not enum_value_ok(value) for value in enum_values)):
            warnings.append(
                Warning(
                    "Choices %s.%s has at least one value that is not lowercased/underscore ascii only"
                    % (klass.__module__, klass.__name__),
                    hint="Lower case the values and replace dashes/spaces with underscores",
                    obj=klass,
                    id="vng_api_common.enums.W001",
                )
            )

    return warnings
