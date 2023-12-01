from django.db.models import TextChoices


def ensure_description_exists(cls):
    descriptions = cls.get_descriptions()

    for choice in cls.choices:
        assert choice in descriptions

    return cls


class TextChoicesWithDescriptions(TextChoices):
    @classmethod
    def get_descriptions(cls):
        return {}
