from datetime import timedelta

from django.core import checks
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from iso639 import languages

from .constants import BSN_LENGTH, RSIN_LENGTH, VertrouwelijkheidsAanduiding
from .validators import validate_rsin

ISO_639_2B = languages.part2b

LANGUAGE_CHOICES = tuple([
    (code, language.name) for code, language in ISO_639_2B.items()
])


class RSINField(models.CharField):
    default_validators = [validate_rsin]
    description = _("RSIN")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', RSIN_LENGTH)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_fixed_max_length_attribute(**kwargs))
        return errors

    def _check_fixed_max_length_attribute(self, **kwargs):
        if self.max_length != RSIN_LENGTH:
            return [
                checks.Error(
                    "RSINField may not override 'max_length' attribute.",
                    obj=self,
                    id='zds_schema.fields.E001',
                )
            ]
        return []


class BSNField(models.CharField):
    default_validators = [validate_rsin]
    description = _("BSN")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', BSN_LENGTH)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_fixed_max_length_attribute(**kwargs))
        return errors

    def _check_fixed_max_length_attribute(self, **kwargs):
        if self.max_length != BSN_LENGTH:
            return [
                checks.Error(
                    "BSNField may not override 'max_length' attribute.",
                    obj=self,
                    id='zds_schema.fields.E002',
                )
            ]
        return []


class LanguageField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 3)
        kwargs.setdefault('choices', LANGUAGE_CHOICES)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_fixed_max_length_attribute(**kwargs))
        errors.extend(self._check_choices(**kwargs))
        return errors

    def _check_fixed_max_length_attribute(self, **kwargs):
        if self.max_length != 3:
            return [
                checks.Error(
                    "LanguageField may not override 'max_length' attribute.",
                    obj=self,
                    id='zds_schema.fields.E003',
                )
            ]
        return []

    def _check_choices(self, **kwargs):
        if self.choices != LANGUAGE_CHOICES:
            return [
                checks.Error(
                    "LanguageField may not override 'choices' attribute.",
                    obj=self,
                    id='zds_schema.fields.E004',
                )
            ]
        return []


class VertrouwelijkheidsAanduidingField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        kwargs.setdefault('choices', VertrouwelijkheidsAanduiding.choices)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_choices(**kwargs))
        return errors

    def _check_choices(self, **kwargs):
        if self.choices != VertrouwelijkheidsAanduiding.choices:
            return [
                checks.Error(
                    "VertrouwelijkheidsAanduidingField may not override 'choices' attribute.",
                    obj=self,
                    id='zds_schema.fields.E005',
                )
            ]
        return []


class DaysDurationField(models.DurationField):
    """
    Express duration in number of calendar days.

    :param min_duration: minimal duration, in number of calendar days.
      Defaults to 1.
    :param max_duration: maximal duration, in number of calendar days.
      Defaults to 999.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('min_duration', 1)
        kwargs.setdefault('max_duration', 999)  # 999 calendar days

        self.min_duration = kwargs.pop('min_duration')
        self.max_duration = kwargs.pop('max_duration')

        self.default_validators = [
            MinValueValidator(timedelta(days=self.min_duration)),
            MaxValueValidator(timedelta(days=self.max_duration))
        ]

        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple:
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({
            'min_duration': self.min_duration,
            'max_duration': self.max_duration,
        })
        return name, path, args, kwargs

    def check(self, **kwargs) -> list:
        errors = super().check(**kwargs)
        errors.extend(self._check_min_duration(**kwargs))
        return errors

    def _check_min_duration(self, **kwargs) -> list:
        errors = []
        if self.min_duration < 1:
            errors.append([
                checks.Error(
                    "De minimale duur in kalenderdagen moet groter dan of gelijk aan 1 zijn",
                    obj=self,
                    id='zds_schema.fields.E006',
                )
            ])
        if self.min_duration > self.max_duration:
            errors.append([
                checks.Error(
                    "De minimale duur mag niet langer zijn dan de maximale duur",
                    obj=self,
                    id='zds_schema.fields.E007',
                )
            ])
        return errors
