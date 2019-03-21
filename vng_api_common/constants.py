from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

BSN_LENGTH = 9
RSIN_LENGTH = 9

VERSION_HEADER = 'API-version'

SCOPE_NOTIFICATIES_PUBLICEREN_LABEL = 'notificaties.scopes.publiceren'


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


class Archiefnominatie(DjangoChoices):
    blijvend_bewaren = ChoiceItem(
        'blijvend_bewaren',
        _("Het zaakdossier moet bewaard blijven en op de Archiefactiedatum overgedragen worden naar een "
          "archiefbewaarplaats.")
    )
    vernietigen = ChoiceItem(
        'vernietigen',
        _("Het zaakdossier moet op of na de Archiefactiedatum vernietigd worden.")
    )


class Archiefstatus(DjangoChoices):
    nog_te_archiveren = ChoiceItem(
        'nog_te_archiveren',
        _("De zaak cq. het zaakdossier is nog niet als geheel gearchiveerd.")
    )
    gearchiveerd = ChoiceItem(
        'gearchiveerd',
        _("De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt.")
    )
    gearchiveerd_procestermijn_onbekend = ChoiceItem(
        'gearchiveerd_procestermijn_onbekend',
        _("De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt maar de vernietigingsdatum "
          "kan nog niet bepaald worden.")
    )
    # After deliberation this element was removed because "vernietigd" means
    # it's really gone and the status wouldn't make sense:
    #
    # vernietigd = ChoiceItem('vernietigd',
    #     _("De zaak cq. het zaakdossier is vernietigd.")
    # )
    overgedragen = ChoiceItem(
        'overgedragen',
        _("De zaak cq. het zaakdossier is overgebracht naar een archiefbewaarplaats.")
    )


class BrondatumArchiefprocedureAfleidingswijze(DjangoChoices):
    afgehandeld = ChoiceItem(
        'afgehandeld', _("Afgehandeld"),
        description=_("De termijn start op de datum waarop de zaak is "
                      "afgehandeld (ZAAK.Einddatum in het RGBZ).")
    )
    ander_datumkenmerk = ChoiceItem(
        'ander_datumkenmerk', _("Ander datumkenmerk"),
        description=_("De termijn start op de datum die is vastgelegd in een "
                      "ander datumveld dan de datumvelden waarop de overige "
                      "waarden (van deze attribuutsoort) betrekking hebben. "
                      "`Objecttype`, `Registratie` en `Datumkenmerk` zijn niet "
                      "leeg.")
    )
    eigenschap = ChoiceItem(
        'eigenschap', _("Eigenschap"),
        description=_("De termijn start op de datum die vermeld is in een "
                      "zaaktype-specifieke eigenschap (zijnde een `datumveld`). "
                      "`ResultaatType.ZaakType` heeft een `Eigenschap`; "
                      "`Objecttype`, en `Datumkenmerk` zijn niet leeg.")
    )
    gerelateerde_zaak = ChoiceItem(
        'gerelateerde_zaak', _("Gerelateerde zaak"),
        description=_("De termijn start op de datum waarop de gerelateerde "
                      "zaak is afgehandeld (`ZAAK.Einddatum` of "
                      "`ZAAK.Gerelateerde_zaak.Einddatum` in het RGBZ). "
                      "`ResultaatType.ZaakType` heeft gerelateerd `ZaakType`")
    )
    hoofdzaak = ChoiceItem(
        'hoofdzaak', _("Hoofzaak"),
        description=_("De termijn start op de datum waarop de gerelateerde "
                      "zaak is afgehandeld, waarvan de zaak een deelzaak is "
                      "(`ZAAK.Einddatum` van de hoofdzaak in het RGBZ). "
                      "ResultaatType.ZaakType is deelzaaktype van ZaakType.")
    )
    ingangsdatum_besluit = ChoiceItem(
        'ingangsdatum_besluit', _("Ingangsdatum besluit"),
        description=_("De termijn start op de datum waarop het besluit van "
                      "kracht wordt (`BESLUIT.Ingangsdatum` in het RGBZ).	"
                      "ResultaatType.ZaakType heeft relevant BesluitType")
    )
    termijn = ChoiceItem(
        'termijn', _("Termijn"),
        description=_("De termijn start een vast aantal jaren na de datum "
                      "waarop de zaak is afgehandeld (`ZAAK.Einddatum` in het "
                      "RGBZ).")
    )
    vervaldatum_besluit = ChoiceItem(
        'vervaldatum_besluit', _("Vervaldatum besluit"),
        description=_("De termijn start op de dag na de datum waarop het "
                      "besluit vervalt (`BESLUIT.Vervaldatum` in het RGBZ). "
                      "ResultaatType.ZaakType heeft relevant BesluitType")
    )
    zaakobject = ChoiceItem(
        'zaakobject', _("Zaakobject"),
        description=_("De termijn start op de einddatum geldigheid van het "
                      "zaakobject waarop de zaak betrekking heeft "
                      "(bijvoorbeeld de overlijdendatum van een Persoon). "
                      "M.b.v. de attribuutsoort `Objecttype` wordt vastgelegd "
                      "om welke zaakobjecttype het gaat; m.b.v. de "
                      "attribuutsoort `Datumkenmerk` wordt vastgelegd welke "
                      "datum-attribuutsoort van het zaakobjecttype het betreft.")
    )


class ZaakobjectTypes(DjangoChoices):
    verblijfs_object = ChoiceItem('VerblijfsObject', 'Verblijfsobject')
    melding_openbare_ruimte = ChoiceItem('MeldingOpenbareRuimte', "Melding openbare ruimte")
    avg_inzage_verzoek = ChoiceItem('InzageVerzoek', "Inzage verzoek in het kader van de AVG")
