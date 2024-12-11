from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.utils.translation import gettext_lazy as _

from vng_api_common.caching import ETagMixin
from vng_api_common.descriptors import GegevensGroepType


class Group(models.Model):
    name = models.CharField(_("name"), max_length=100)

    subgroup_field_1 = models.CharField(max_length=50, blank=True)
    subgroup_field_2 = models.CharField(max_length=50, blank=True, default="baz")

    subgroup = GegevensGroepType(
        {"field_1": subgroup_field_1, "field_2": subgroup_field_2},
        optional=("field_2",),
    )


class Person(ETagMixin, models.Model):
    name = models.CharField(_("name"), max_length=50)

    address_street = models.CharField(_("street name"), max_length=255)
    address_number = models.CharField(_("house number"), max_length=10)

    address = GegevensGroepType(
        {"street": address_street, "number": address_number}, required=False
    )

    group = models.ForeignKey("Group", null=True, on_delete=models.CASCADE)

    hobbies = models.ManyToManyField("Hobby", related_name="people", blank=True)


class Hobby(ETagMixin, models.Model):
    name = models.CharField(_("name"), max_length=100)


class Record(models.Model):
    identificatie = models.CharField(_("identificatie"), max_length=50, unique=True)
    create_date = models.DateField(_("create date"))


class PolyChoice(models.TextChoices):
    hobby = "hobby", _("Hobby.")
    record = "record", _("Record")


class Poly(models.Model):
    name = models.CharField(_("name"), max_length=100)
    choice = models.CharField(_("choice"), choices=PolyChoice.choices, max_length=6)


class FkModel(models.Model):
    name = models.CharField(_("name"), max_length=100)
    field_with_underscores = models.CharField(_("name"), max_length=100)
    poly = models.ForeignKey(
        verbose_name=_("poly"),
        on_delete=models.deletion.CASCADE,
        to=Poly,
    )


class MediaFileModel(models.Model):
    name = models.CharField(_("name"), max_length=100)
    file = models.FileField(
        _("file"),
        upload_to="uploads/",
    )


class GeometryModel(models.Model):
    name = models.CharField(_("name"), max_length=100)
    zaakgeometrie = GeometryField(
        blank=True,
        null=True,
        help_text="Punt, lijn of (multi-)vlak geometrie-informatie.",
    )
