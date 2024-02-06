import re

from django.db.models import TextChoices

import pytest

from vng_api_common.choices import (
    TextChoicesWithDescriptions,
    ensure_description_exists,
)
from vng_api_common.serializers import add_choice_values_help_text


class NormalChoices(TextChoices):
    option1 = "option1", "option one name"
    option2 = "option2", "option two name"


class ChoicesWithDescriptions(TextChoicesWithDescriptions):
    option1 = "option1", "option one name"
    option2 = "option2", "option two name"

    @classmethod
    def descriptions(cls):
        return {
            ChoicesWithDescriptions.option1: "Option one description",
            ChoicesWithDescriptions.option2: "Description of option two",
        }


def test_add_choice_values_help_text():
    help_text = add_choice_values_help_text(NormalChoices)
    expected_text = (
        "Uitleg bij mogelijke waarden:\n\n"
        "* `option1` - option one name\n"
        "* `option2` - option two name"
    )
    assert help_text == expected_text


def test_add_choice_values_help_text_with_descriptions():
    help_text = add_choice_values_help_text(ChoicesWithDescriptions)
    expected_text = (
        "Uitleg bij mogelijke waarden:\n\n"
        "* `option1` - (option one name) Option one description\n"
        "* `option2` - (option two name) Description of option two"
    )
    assert help_text == expected_text


def test_add_choice_values_help_text_with_tuple():
    choices = (("option1", "option one name"), ("option2", "option two name"))

    help_text = add_choice_values_help_text(choices)
    expected_text = (
        "Uitleg bij mogelijke waarden:\n\n"
        "* `option1` - option one name\n"
        "* `option2` - option two name"
    )
    assert help_text == expected_text


def test_text_choice_with_descriptions_validator():
    class BadChoicesWithDescriptions(TextChoicesWithDescriptions):
        option1 = "option1", "option one name"
        option2 = "option2", "option two name"

        @classmethod
        def descriptions(cls):
            return {
                ChoicesWithDescriptions.option1: "Option one description",
                # ChoicesWithDescriptions.option2: "Description of option two",
            }

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Choice (option2, option two name) in BadChoicesWithDescriptions is missing a description"
        ),
    ):
        ensure_description_exists(BadChoicesWithDescriptions)


def test_text_choice_with_descriptions_validator_recursion():
    class TextChoiceSubclass(TextChoicesWithDescriptions):
        @classmethod
        def descriptions(cls):
            return {}

    class BadChoicesSubclassWithDescriptions(TextChoiceSubclass):
        option1 = "option1", "option one name"
        option2 = "option2", "option two name"

        @classmethod
        def descriptions(cls):
            return {
                ChoicesWithDescriptions.option1: "Option one description",
                # ChoicesWithDescriptions.option2: "Description of option two",
            }

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Choice (option2, option two name) in BadChoicesSubclassWithDescriptions is missing a description"
        ),
    ):
        ensure_description_exists(BadChoicesSubclassWithDescriptions)
