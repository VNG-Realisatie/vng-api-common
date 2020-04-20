from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.descriptors import GegevensGroepType


class Group(models.Model):
    subgroup_field_1 = models.CharField(max_length=50, blank=True)
    subgroup_field_2 = models.CharField(max_length=50, blank=True, default="baz")

    subgroup = GegevensGroepType(
        {"field_1": subgroup_field_1, "field_2": subgroup_field_2},
        optional=("field_2",),
    )


class Person(models.Model):
    name = models.CharField(_("name"), max_length=50)

    address_street = models.CharField(_("street name"), max_length=255)
    address_number = models.CharField(_("house number"), max_length=10)

    address = GegevensGroepType({"street": address_street, "number": address_number}, required=False)

    group = models.ForeignKey("Group", null=True, on_delete=models.CASCADE)
