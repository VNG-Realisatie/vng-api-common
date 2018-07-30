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
