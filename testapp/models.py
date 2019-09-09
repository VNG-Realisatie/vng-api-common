from django.db import models
from django.utils.translation import ugettext_lazy as _

from vng_api_common.caching import ETagMixin
from vng_api_common.descriptors import GegevensGroepType


class Group(models.Model):
    name = models.CharField(_("name"), max_length=100)


class Person(ETagMixin, models.Model):
    name = models.CharField(_("name"), max_length=50)

    address_street = models.CharField(_("street name"), max_length=255)
    address_number = models.CharField(_("house number"), max_length=10)

    address = GegevensGroepType({"street": address_street, "number": address_number})

    group = models.ForeignKey("Group", null=True, on_delete=models.CASCADE)

    hobbies = models.ManyToManyField("Hobby", related_name="people", blank=True)


class Hobby(ETagMixin, models.Model):
    name = models.CharField(_("name"), max_length=100)
