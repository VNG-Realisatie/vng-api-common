from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _

BSN_LENGTH = 9
RSIN_LENGTH = 9

VERSION_HEADER = "API-version"

HEADER_AUDIT = "X-Audit-Toelichting"
HEADER_LOGRECORD_ID = "X-NLX-Logrecord-ID"

FILTER_URL_DID_NOT_RESOLVE = "NO_MATCHING_OBJECT"

# constants for ObjectInformatieObjectTypes
BESLUIT_CONST = "besluit"
BESLUIT_CHOICE = BESLUIT_CONST, _("Besluit")

ZAAK_CONST = "zaak"
ZAAK_CHOICE = ZAAK_CONST, _("Zaak")

VERZOEK_CONST = "verzoek"
VERZOEK_CHOICE = VERZOEK_CONST, _("Verzoek")


class VertrouwelijkheidsAanduiding(models.TextChoices):
    openbaar = "openbaar", _("Openbaar")
    beperkt_openbaar = "beperkt_openbaar", _("Beperkt openbaar")
    intern = "intern", _("Intern")
    zaakvertrouwelijk = "zaakvertrouwelijk", _("Zaakvertrouwelijk")
    vertrouwelijk = "vertrouwelijk", _("Vertrouwelijk")
    confidentieel = "confidentieel", _("Confidentieel")
    geheim = "geheim", _("Geheim")
    zeer_geheim = "zeer_geheim", _("Zeer geheim")

    @classmethod
    def get_order_expression(cls, field_name):
        whens = []
        for order, value in enumerate(cls.values):
            whens.append(
                models.When(**{field_name: value, "then": models.Value(order)})
            )
        return models.Case(*whens, output_field=models.IntegerField())

    @classmethod
    def get_choice_order(cls, value) -> Optional[int]:
        orders = {
            value: order
            for order, value in enumerate(VertrouwelijkheidsAanduiding.values)
        }
        return orders.get(value)


class RolOmschrijving(models.TextChoices):
    adviseur = "adviseur", _("Adviseur")
    behandelaar = "behandelaar", _("Behandelaar")
    belanghebbende = "belanghebbende", _("Belanghebbende")
    beslisser = "beslisser", _("Beslisser")
    initiator = "initiator", _("Initiator")
    klantcontacter = "klantcontacter", _("Klantcontacter")
    zaakcoordinator = "zaakcoordinator", _("Zaakcoördinator")
    medeinitiator = "mede_initiator", _("Mede-initiator")


class RolTypes(models.TextChoices):
    natuurlijk_persoon = "natuurlijk_persoon", _("Natuurlijk persoon")
    niet_natuurlijk_persoon = "niet_natuurlijk_persoon", _("Niet-natuurlijk persoon")
    vestiging = "vestiging", _("Vestiging")
    organisatorische_eenheid = "organisatorische_eenheid", _("Organisatorische eenheid")
    medewerker = "medewerker", _("Medewerker")


class Archiefnominatie(models.TextChoices):
    blijvend_bewaren = "blijvend_bewaren", _(
        "Het zaakdossier moet bewaard blijven en op de Archiefactiedatum "
        "overgedragen worden naar een archiefbewaarplaats."
    )
    vernietigen = "vernietigen", _(
        "Het zaakdossier moet op of na de Archiefactiedatum vernietigd worden."
    )


class Archiefstatus(models.TextChoices):
    nog_te_archiveren = "nog_te_archiveren", _(
        "De zaak cq. het zaakdossier is nog niet als geheel gearchiveerd."
    )
    gearchiveerd = "gearchiveerd", _(
        "De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt."
    )
    gearchiveerd_procestermijn_onbekend = "gearchiveerd_procestermijn_onbekend", _(
        "De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt "
        "maar de vernietigingsdatum kan nog niet bepaald worden."
    )
    overgedragen = "overgedragen", _(
        "De zaak cq. het zaakdossier is overgebracht naar een archiefbewaarplaats."
    )


class BrondatumArchiefprocedureAfleidingswijze(models.TextChoices):
    afgehandeld = "afgehandeld", _("Afgehandeld")
    ander_datumkenmerk = "ander_datumkenmerk", _("Ander datumkenmerk")
    eigenschap = "eigenschap", _("Eigenschap")
    gerelateerde_zaak = "gerelateerde_zaak", _("Gerelateerde zaak")
    hoofdzaak = "hoofdzaak", _("Hoofdzaak")
    ingangsdatum_besluit = "ingangsdatum_besluit", _("Ingangsdatum besluit")
    termijn = "termijn", _("Termijn")
    vervaldatum_besluit = "vervaldatum_besluit", _("Vervaldatum besluit")
    zaakobject = "zaakobject", _("Zaakobject")


class ZaakobjectTypes(models.TextChoices):
    adres = "adres", _("Adres")
    besluit = "besluit", _("Besluit")
    buurt = "buurt", _("Buurt")
    enkelvoudig_document = "enkelvoudig_document", _("Enkelvoudig document")
    gemeente = "gemeente", _("Gemeente")
    gemeentelijke_openbare_ruimte = "gemeentelijke_openbare_ruimte", _(
        "Gemeentelijke openbare ruimte"
    )
    huishouden = "huishouden", _("Huishouden")
    inrichtingselement = "inrichtingselement", _("Inrichtingselement")
    kadastrale_onroerende_zaak = "kadastrale_onroerende_zaak", _(
        "Kadastrale onroerende zaak"
    )
    kunstwerkdeel = "kunstwerkdeel", _("Kunstwerkdeel")
    maatschappelijke_activiteit = "maatschappelijke_activiteit", _(
        "Maatschappelijke activiteit"
    )
    medewerker = "medewerker", _("Medewerker")
    natuurlijk_persoon = "natuurlijk_persoon", _("Natuurlijk persoon")
    niet_natuurlijk_persoon = "niet_natuurlijk_persoon", _("Niet-natuurlijk persoon")
    openbare_ruimte = "openbare_ruimte", _("Openbare ruimte")
    organisatorische_eenheid = "organisatorische_eenheid", _("Organisatorische eenheid")
    pand = "pand", _("Pand")
    spoorbaandeel = "spoorbaandeel", _("Spoorbaandeel")
    status = "status", _("Status")
    terreindeel = "terreindeel", _("Terreindeel")
    terrein_gebouwd_object = "terrein_gebouwd_object", _("Terrein gebouwd object")
    vestiging = "vestiging", _("Vestiging")
    waterdeel = "waterdeel", _("Waterdeel")
    wegdeel = "wegdeel", _("Wegdeel")
    wijk = "wijk", _("Wijk")
    woonplaats = "woonplaats", _("Woonplaats")
    woz_deelobject = "woz_deelobject", _("Woz deel object")
    woz_object = "woz_object", _("Woz object")
    woz_waarde = "woz_waarde", _("Woz waarde")
    zakelijk_recht = "zakelijk_recht", _("Zakelijk recht")
    overige = "overige", _("Overige")


class ComponentTypes(models.TextChoices):
    ac = "ac", _("Autorisaties API")
    nrc = "nrc", _("Notificaties API")
    zrc = "zrc", _("Zaken API")
    ztc = "ztc", _("Catalogi API")
    drc = "drc", _("Documenten API")
    brc = "brc", _("Besluiten API")
    cmc = "cmc", _("Contactmomenten API")
    kc = "kc", _("Klanten API")
    vrc = "vrc", _("Verzoeken API")


class CommonResourceAction(models.TextChoices):
    create = "create", _("Object aangemaakt")
    list = "list", _("Lijst van objecten opgehaald")
    retrieve = "retrieve", _("Object opgehaald")
    destroy = "destroy", _("Object verwijderd")
    update = "update", _("Object bijgewerkt")
    partial_update = "partial_update", _("Object deels bijgewerkt")


class RelatieAarden(models.TextChoices):
    hoort_bij = "hoort_bij", _("Hoort bij, omgekeerd: kent")
    legt_vast = "legt_vast", _("Legt vast, omgekeerd: kan vastgelegd zijn als")

    @classmethod
    def from_object_type(cls, object_type: str) -> str:
        if object_type == "zaak":
            return cls.hoort_bij

        if object_type == "besluit":
            return cls.legt_vast

        raise ValueError(f"Unknown object_type '{object_type}'")
