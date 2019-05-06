from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AuditTrailAction(DjangoChoices):
    create = ChoiceItem('create', _("De resource is aangemaakt"))
    get = ChoiceItem('get', _("De gegevens van de resource zijn opgehaald"))
    delete = ChoiceItem('delete', _("De resource is verwijderd"))
    update = ChoiceItem('update', _("De gegevens van de resource zijn bijgewerkt"))
    partial_update = ChoiceItem('partial_update', _("De gegevens van de resource zijn deels bijgewerkt"))
