from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

BSN_LENGTH = 9
RSIN_LENGTH = 9


class VertrouwelijkheidsAanduiding(DjangoChoices):
    openbaar = ChoiceItem('openbaar', 'OPENBAAR')
    beperkt_openbaar = ChoiceItem('beperkt openbaar', 'BEPERKT OPENBAAR')
    intern = ChoiceItem('intern', 'INTERN')
    zaakvertrouwelijk = ChoiceItem('zaakvertrouwelijk', 'ZAAKVERTROUWELIJK')
    vertrouwelijk = ChoiceItem('vertrouwelijk', 'VERTROUWELIJK')
    confidentieel = ChoiceItem('confidentieel', 'CONFIDENTIEEL')
    geheim = ChoiceItem('geheim', 'GEHEIM')
    zeer_geheim = ChoiceItem('zeer geheim', 'ZEER GEHEIM')


class RolOmschrijving(DjangoChoices):
    adviseur = ChoiceItem(
        'Adviseur', 'Adviseur',
        description='Kennis in dienst stellen van de behandeling van (een deel van) een zaak.'
    )
    behandelaar = ChoiceItem(
        'Behandelaar', 'Behandelaar',
        description='De vakinhoudelijke behandeling doen van (een deel van) een zaak.'
    )
    belanghebbende = ChoiceItem(
        'Belanghebbende', 'Belanghebbende',
        description='Vanuit eigen en objectief belang rechtstreeks betrokken '
                    'zijn bij de behandeling en/of de uitkomst van een zaak.'
    )
    beslisser = ChoiceItem(
        'Beslisser', 'Beslisser',
        description='Nemen van besluiten die voor de uitkomst van een zaak noodzakelijk zijn.'
    )
    initiator = ChoiceItem(
        'Initiator', 'Initiator',
        description='Aanleiding geven tot de start van een zaak ..'
    )
    klantcontacter = ChoiceItem(
        'Klantcontacter', 'Klantcontacter',
        description='Het eerste aanspreekpunt zijn voor vragen van burgers en bedrijven ..'
    )
    zaakcoordinator = ChoiceItem(
        'Zaakcoördinator', 'Zaakcoördinator',
        description='Er voor zorg dragen dat de behandeling van de zaak in samenhang '
                    'uitgevoerd wordt conform de daarover gemaakte afspraken.'
    )
    medeinitiator = ChoiceItem(
        'Mede-initiator', 'Mede-initiator',
        description=''
    )


class RolTypes(DjangoChoices):
    natuurlijk_persoon = ChoiceItem('Natuurlijk persoon', "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem('Niet-natuurlijk persoon', "Niet-natuurlijk persoon")
    vestiging = ChoiceItem('Vestiging', "Vestiging")
    organisatorische_eenheid = ChoiceItem('Organisatorische eenheid', "Organisatorische eenheid")
    medewerker = ChoiceItem('Medewerker', "Medewerker")


class ObjectTypes(DjangoChoices):
    besluit = ChoiceItem('besluit', _("Besluit"))
    zaak = ChoiceItem('zaak', _("Zaak"))
