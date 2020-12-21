from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

BSN_LENGTH = 9
RSIN_LENGTH = 9

VERSION_HEADER = "API-version"

SCOPE_NOTIFICATIES_PUBLICEREN_LABEL = "notificaties.scopes.publiceren"

HEADER_AUDIT = "X-Audit-Toelichting"
HEADER_LOGRECORD_ID = "X-NLX-Logrecord-ID"

FILTER_URL_DID_NOT_RESOLVE = "NO_MATCHING_OBJECT"


class VertrouwelijkheidsAanduiding(DjangoChoices):
    openbaar = ChoiceItem("openbaar", "Openbaar")
    beperkt_openbaar = ChoiceItem("beperkt_openbaar", "Beperkt openbaar")
    intern = ChoiceItem("intern", "Intern")
    zaakvertrouwelijk = ChoiceItem("zaakvertrouwelijk", "Zaakvertrouwelijk")
    vertrouwelijk = ChoiceItem("vertrouwelijk", "Vertrouwelijk")
    confidentieel = ChoiceItem("confidentieel", "Confidentieel")
    geheim = ChoiceItem("geheim", "Geheim")
    zeer_geheim = ChoiceItem("zeer_geheim", "Zeer geheim")


class RolOmschrijving(DjangoChoices):
    adviseur = ChoiceItem(
        "adviseur",
        "Adviseur",
        description="Kennis in dienst stellen van de behandeling van (een deel van) een zaak.",
    )
    behandelaar = ChoiceItem(
        "behandelaar",
        "Behandelaar",
        description="De vakinhoudelijke behandeling doen van (een deel van) een zaak.",
    )
    belanghebbende = ChoiceItem(
        "belanghebbende",
        "Belanghebbende",
        description="Vanuit eigen en objectief belang rechtstreeks betrokken "
        "zijn bij de behandeling en/of de uitkomst van een zaak.",
    )
    beslisser = ChoiceItem(
        "beslisser",
        "Beslisser",
        description="Nemen van besluiten die voor de uitkomst van een zaak noodzakelijk zijn.",
    )
    initiator = ChoiceItem(
        "initiator",
        "Initiator",
        description="Aanleiding geven tot de start van een zaak ..",
    )
    klantcontacter = ChoiceItem(
        "klantcontacter",
        "Klantcontacter",
        description="Het eerste aanspreekpunt zijn voor vragen van burgers en bedrijven ..",
    )
    zaakcoordinator = ChoiceItem(
        "zaakcoordinator",
        "Zaakcoördinator",
        description="Er voor zorg dragen dat de behandeling van de zaak in samenhang "
        "uitgevoerd wordt conform de daarover gemaakte afspraken.",
    )
    medeinitiator = ChoiceItem("mede_initiator", "Mede-initiator", description="")


class RolTypes(DjangoChoices):
    natuurlijk_persoon = ChoiceItem("natuurlijk_persoon", "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem(
        "niet_natuurlijk_persoon", "Niet-natuurlijk persoon"
    )
    vestiging = ChoiceItem("vestiging", "Vestiging")
    organisatorische_eenheid = ChoiceItem(
        "organisatorische_eenheid", "Organisatorische eenheid"
    )
    medewerker = ChoiceItem("medewerker", "Medewerker")


class ObjectTypes(DjangoChoices):
    besluit = ChoiceItem("besluit", _("Besluit"))
    zaak = ChoiceItem("zaak", _("Zaak"))


class Archiefnominatie(DjangoChoices):
    blijvend_bewaren = ChoiceItem(
        "blijvend_bewaren",
        _(
            "Het zaakdossier moet bewaard blijven en op de Archiefactiedatum overgedragen worden naar een "
            "archiefbewaarplaats."
        ),
    )
    vernietigen = ChoiceItem(
        "vernietigen",
        _("Het zaakdossier moet op of na de Archiefactiedatum vernietigd worden."),
    )


class Archiefstatus(DjangoChoices):
    nog_te_archiveren = ChoiceItem(
        "nog_te_archiveren",
        _("De zaak cq. het zaakdossier is nog niet als geheel gearchiveerd."),
    )
    gearchiveerd = ChoiceItem(
        "gearchiveerd",
        _(
            "De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt."
        ),
    )
    gearchiveerd_procestermijn_onbekend = ChoiceItem(
        "gearchiveerd_procestermijn_onbekend",
        _(
            "De zaak cq. het zaakdossier is als geheel niet-wijzigbaar bewaarbaar gemaakt maar de vernietigingsdatum "
            "kan nog niet bepaald worden."
        ),
    )
    # After deliberation this element was removed because "vernietigd" means
    # it's really gone and the status wouldn't make sense:
    #
    # vernietigd = ChoiceItem('vernietigd',
    #     _("De zaak cq. het zaakdossier is vernietigd.")
    # )
    overgedragen = ChoiceItem(
        "overgedragen",
        _("De zaak cq. het zaakdossier is overgebracht naar een archiefbewaarplaats."),
    )


class BrondatumArchiefprocedureAfleidingswijze(DjangoChoices):
    afgehandeld = ChoiceItem(
        "afgehandeld",
        _("Afgehandeld"),
        description=_(
            "De termijn start op de datum waarop de zaak is "
            "afgehandeld (ZAAK.Einddatum in het RGBZ)."
        ),
    )
    ander_datumkenmerk = ChoiceItem(
        "ander_datumkenmerk",
        _("Ander datumkenmerk"),
        description=_(
            "De termijn start op de datum die is vastgelegd in een "
            "ander datumveld dan de datumvelden waarop de overige "
            "waarden (van deze attribuutsoort) betrekking hebben. "
            "`Objecttype`, `Registratie` en `Datumkenmerk` zijn niet "
            "leeg."
        ),
    )
    eigenschap = ChoiceItem(
        "eigenschap",
        _("Eigenschap"),
        description=_(
            "De termijn start op de datum die vermeld is in een "
            "zaaktype-specifieke eigenschap (zijnde een `datumveld`). "
            "`ResultaatType.ZaakType` heeft een `Eigenschap`; "
            "`Objecttype`, en `Datumkenmerk` zijn niet leeg."
        ),
    )
    gerelateerde_zaak = ChoiceItem(
        "gerelateerde_zaak",
        _("Gerelateerde zaak"),
        description=_(
            "De termijn start op de datum waarop de gerelateerde "
            "zaak is afgehandeld (`ZAAK.Einddatum` of "
            "`ZAAK.Gerelateerde_zaak.Einddatum` in het RGBZ). "
            "`ResultaatType.ZaakType` heeft gerelateerd `ZaakType`"
        ),
    )
    hoofdzaak = ChoiceItem(
        "hoofdzaak",
        _("Hoofdzaak"),
        description=_(
            "De termijn start op de datum waarop de gerelateerde "
            "zaak is afgehandeld, waarvan de zaak een deelzaak is "
            "(`ZAAK.Einddatum` van de hoofdzaak in het RGBZ). "
            "ResultaatType.ZaakType is deelzaaktype van ZaakType."
        ),
    )
    ingangsdatum_besluit = ChoiceItem(
        "ingangsdatum_besluit",
        _("Ingangsdatum besluit"),
        description=_(
            "De termijn start op de datum waarop het besluit van "
            "kracht wordt (`BESLUIT.Ingangsdatum` in het RGBZ).	"
            "ResultaatType.ZaakType heeft relevant BesluitType"
        ),
    )
    termijn = ChoiceItem(
        "termijn",
        _("Termijn"),
        description=_(
            "De termijn start een vast aantal jaren na de datum "
            "waarop de zaak is afgehandeld (`ZAAK.Einddatum` in het "
            "RGBZ)."
        ),
    )
    vervaldatum_besluit = ChoiceItem(
        "vervaldatum_besluit",
        _("Vervaldatum besluit"),
        description=_(
            "De termijn start op de dag na de datum waarop het "
            "besluit vervalt (`BESLUIT.Vervaldatum` in het RGBZ). "
            "ResultaatType.ZaakType heeft relevant BesluitType"
        ),
    )
    zaakobject = ChoiceItem(
        "zaakobject",
        _("Zaakobject"),
        description=_(
            "De termijn start op de einddatum geldigheid van het "
            "zaakobject waarop de zaak betrekking heeft "
            "(bijvoorbeeld de overlijdendatum van een Persoon). "
            "M.b.v. de attribuutsoort `Objecttype` wordt vastgelegd "
            "om welke zaakobjecttype het gaat; m.b.v. de "
            "attribuutsoort `Datumkenmerk` wordt vastgelegd welke "
            "datum-attribuutsoort van het zaakobjecttype het betreft."
        ),
    )


class ZaakobjectTypes(DjangoChoices):
    adres = ChoiceItem("adres", "Adres")
    besluit = ChoiceItem("besluit", "Besluit")
    buurt = ChoiceItem("buurt", "Buurt")
    enkelvoudig_document = ChoiceItem("enkelvoudig_document", "Enkelvoudig document")
    gemeente = ChoiceItem("gemeente", "Gemeente")
    gemeentelijke_openbare_ruimte = ChoiceItem(
        "gemeentelijke_openbare_ruimte", "Gemeentelijke openbare ruimte"
    )
    huishouden = ChoiceItem("huishouden", "Huishouden")
    inrichtingselement = ChoiceItem("inrichtingselement", "Inrichtingselement")
    kadastrale_onroerende_zaak = ChoiceItem(
        "kadastrale_onroerende_zaak", "Kadastrale onroerende zaak"
    )
    kunstwerkdeel = ChoiceItem("kunstwerkdeel", "Kunstwerkdeel")
    maatschappelijke_activiteit = ChoiceItem(
        "maatschappelijke_activiteit", "Maatschappelijke activiteit"
    )
    medewerker = ChoiceItem("medewerker", "Medewerker")
    natuurlijk_persoon = ChoiceItem("natuurlijk_persoon", "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem(
        "niet_natuurlijk_persoon", "Niet-natuurlijk persoon"
    )
    openbare_ruimte = ChoiceItem("openbare_ruimte", "Openbare ruimte")
    organisatorische_eenheid = ChoiceItem(
        "organisatorische_eenheid", "Organisatorische eenheid"
    )
    pand = ChoiceItem("pand", "Pand")
    spoorbaandeel = ChoiceItem("spoorbaandeel", "Spoorbaandeel")
    status = ChoiceItem("status", "Status")
    terreindeel = ChoiceItem("terreindeel", "Terreindeel")
    terrein_gebouwd_object = ChoiceItem(
        "terrein_gebouwd_object", "Terrein gebouwd object"
    )
    vestiging = ChoiceItem("vestiging", "Vestiging")
    waterdeel = ChoiceItem("waterdeel", "Waterdeel")
    wegdeel = ChoiceItem("wegdeel", "Wegdeel")
    wijk = ChoiceItem("wijk", "Wijk")
    woonplaats = ChoiceItem("woonplaats", "Woonplaats")
    woz_deelobject = ChoiceItem("woz_deelobject", "Woz deel object")
    woz_object = ChoiceItem("woz_object", "Woz object")
    woz_waarde = ChoiceItem("woz_waarde", "Woz waarde")
    zakelijk_recht = ChoiceItem("zakelijk_recht", "Zakelijk recht")
    overige = ChoiceItem("overige", "Overige")


class ComponentTypes(DjangoChoices):
    ac = ChoiceItem("ac", "Autorisaties API")
    nrc = ChoiceItem("nrc", "Notificaties API")
    zrc = ChoiceItem("zrc", "Zaken API")
    ztc = ChoiceItem("ztc", "Catalogi API")
    drc = ChoiceItem("drc", "Documenten API")
    brc = ChoiceItem("brc", "Besluiten API")


class CommonResourceAction(DjangoChoices):
    create = ChoiceItem("create", _("Object aangemaakt"))
    list = ChoiceItem("list", _("Lijst van objecten opgehaald"))
    retrieve = ChoiceItem("retrieve", _("Object opgehaald"))
    destroy = ChoiceItem("destroy", _("Object verwijderd"))
    update = ChoiceItem("update", _("Object bijgewerkt"))
    partial_update = ChoiceItem("partial_update", _("Object deels bijgewerkt"))


class RelatieAarden(DjangoChoices):
    hoort_bij = ChoiceItem("hoort_bij", _("Hoort bij, omgekeerd: kent"))
    legt_vast = ChoiceItem(
        "legt_vast", _("Legt vast, omgekeerd: kan vastgelegd zijn als")
    )

    @classmethod
    def from_object_type(cls, object_type: str) -> str:
        if object_type == ObjectTypes.zaak:
            return cls.hoort_bij

        if object_type == ObjectTypes.besluit:
            return cls.legt_vast

        raise ValueError(f"Unknown object_type '{object_type}'")
