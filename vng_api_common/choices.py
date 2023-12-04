from django.db.models import TextChoices


def ensure_description_exists(cls):
    descriptions = cls.get_descriptions()

    for choice, text in cls.choices:
        if choice not in descriptions:
            raise ValueError(
                f"Choice ({choice}, {text}) in {cls.__name__} is missing a description"
            )
    return cls


class TextChoicesWithDescriptions(TextChoices):
    @classmethod
    def get_descriptions(cls):
        return {}
