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
    adviseur = ChoiceItem('Adviseur', 'Adviseur')
    behandelaar = ChoiceItem('Behandelaar', 'Behandelaar')
    belanghebbende = ChoiceItem('Belanghebbende', 'Belanghebbende')
    beslisser = ChoiceItem('Beslisser', 'Beslisser')
    initiator = ChoiceItem('Initiator', 'Initiator')
    klantcontacter = ChoiceItem('Klantcontacter', 'Klantcontacter')
    zaakcoordinator = ChoiceItem('Zaakcoördinator', 'Zaakcoördinator')


class RolOmschrijvingGeneriek(RolOmschrijving):
    medeinitiator = ChoiceItem('Mede-initiator', 'Mede-initiator')


class RolTypes(DjangoChoices):
    natuurlijk_persoon = ChoiceItem('Natuurlijk persoon', "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem('Niet-natuurlijk persoon', "Niet-natuurlijk persoon")
    vestiging = ChoiceItem('Vestiging', "Vestiging")
    organisatorische_eenheid = ChoiceItem('Organisatorische eenheid', "Organisatorische eenheid")
    medewerker = ChoiceItem('Medewerker', "Medewerker")
