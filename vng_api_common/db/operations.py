from typing import Callable

from django.db import migrations

from ..constants import (
    ComponentTypes,
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduiding,
    ZaakobjectTypes,
)

VERTROUWELIJKHEIDSAANDUIDING_MAPPING = {
    "beperkt openbaar": VertrouwelijkheidsAanduiding.beperkt_openbaar,
    "zeer geheimp": VertrouwelijkheidsAanduiding.zeer_geheim,
}


ROLOMSCHRIJVING_MAPPING = {
    "Adviseur": RolOmschrijving.adviseur,
    "Behandelaar": RolOmschrijving.behandelaar,
    "Belanghebbende": RolOmschrijving.belanghebbende,
    "Beslisser": RolOmschrijving.beslisser,
    "Initiator": RolOmschrijving.initiator,
    "Klantcontacter": RolOmschrijving.klantcontacter,
    "Zaakcoördinator": RolOmschrijving.zaakcoordinator,
    "Mede-initiator": RolOmschrijving.medeinitiator,
}


ROLTYPES_MAPPING = {
    "Natuurlijk persoon": RolTypes.natuurlijk_persoon,
    "Niet-natuurlijk persoon": RolTypes.niet_natuurlijk_persoon,
    "Vestiging": RolTypes.vestiging,
    "Organisatorische eenheid": RolTypes.organisatorische_eenheid,
    "Medewerker": RolTypes.medewerker,
}


ZAAKOBJECTTYPES_MAPPING = {
    "enkelvoudigDocument": ZaakobjectTypes.enkelvoudig_document,
    "gemeentelijkeOpenbareRuimte": ZaakobjectTypes.gemeentelijke_openbare_ruimte,
    "kadastraleOnroerendeZaak": ZaakobjectTypes.kadastrale_onroerende_zaak,
    "maatschappelijkeActiviteit": ZaakobjectTypes.maatschappelijke_activiteit,
    "natuurlijkPersoon": ZaakobjectTypes.natuurlijk_persoon,
    "nietNatuurlijkPersoon": ZaakobjectTypes.niet_natuurlijk_persoon,
    "openbareRuimte": ZaakobjectTypes.openbare_ruimte,
    "organisatorischeEenheid": ZaakobjectTypes.organisatorische_eenheid,
    "terreinGebouwdObject": ZaakobjectTypes.terrein_gebouwd_object,
    "wozDeelobject": ZaakobjectTypes.woz_deelobject,
    "wozObject": ZaakobjectTypes.woz_object,
    "wozWaarde": ZaakobjectTypes.woz_waarde,
    "zakelijkRecht": ZaakobjectTypes.zakelijk_recht,
}


COMPONENTTYPES_MAPPING = {
    "AC": ComponentTypes.ac,
    "NRC": ComponentTypes.nrc,
    "ZRC": ComponentTypes.zrc,
    "ZTC": ComponentTypes.ztc,
    "DRC": ComponentTypes.drc,
    "BRC": ComponentTypes.brc,
}


def update_factory(model: str, field: str, mapping: dict) -> Callable:
    def operation(apps, schema_editor):
        Model = apps.get_model(model)
        for old_value, new_value in mapping.items():
            qs = Model.objects.filter(**{field: old_value})
            qs.update(**{field: new_value})

    return operation


class UpdateChoiceValues(migrations.RunPython):
    mapping: dict

    def __init__(self, model: str, field: str, *args, **kwargs):
        forward = update_factory(model, field, self.mapping)
        backwards = update_factory(
            model, field, {value: key for key, value in self.mapping.items()}
        )

        super().__init__(forward, backwards, *args, **kwargs)


class VertrouwelijkheidsaanduidingUpdate(UpdateChoiceValues):
    mapping = VERTROUWELIJKHEIDSAANDUIDING_MAPPING


class RolomschrijvingUpdate(UpdateChoiceValues):
    mapping = ROLOMSCHRIJVING_MAPPING


class RoltypesUpdate(UpdateChoiceValues):
    mapping = ROLTYPES_MAPPING


class ZaakobjecttypesUpdate(UpdateChoiceValues):
    mapping = ZAAKOBJECTTYPES_MAPPING


class ComponenttypesUpdate(UpdateChoiceValues):
    mapping = COMPONENTTYPES_MAPPING
