==========================================
VNG-API-common - Tooling voor RESTful APIs
==========================================

VNG-API-common biedt generieke implementaties en tooling voor RESTful APIs
in een Common Ground gegevenslandschap.

De tooling wordt o.a. gebruikt in de referentie-implementaties van componenten
voor zaakgericht werken, maar ook in VNG-APIs voor referentielijsten en de
Gemeentelijke Selectielijst.

Het is een third-party library voor Django projecten, gebaseerd op Django Rest
Framework en drf-yasg voor schema-generatie.

.. contents::

.. section-numbering::

Features
========

* Centraal beheer van constanten die de verschillende componenten overstijgen
* GeoJSON OpenAPI definities
* Support voor Geo CRS negotation
* Ingebouwde support voor nested viewsets met declaratievere syntax voor
  registratie
* Vaak voorkomende validators:
    * RSIN/BSN validator
    * Numerieke waarde validator
    * Niet-negatieve waarde validator
    * Alfanumerieke waarde (zonder diacritics)
    * URL-validator (test dat URL bestaat) met pluggable link-checker
    * ``UntilNowValidator`` - valideer datetimes tot en met *nu*.
    * ``UniekeIdentificatieValidator`` (in combinatie met organisatie)
    * ``InformatieObjectUniqueValidator`` om te valideren dat M2M entries
      slechts eenmalig voorkomen
    * ``ObjectInformatieObjectValidator`` om te valideren dat de synchronisatie
      van een object-informatieobject relatie pas kan nadat deze relatie in het
      DRC gemaakt is
    * ``IsImmutableValidator`` - valideer dat bepaalde velden niet gewijzigd
      worden bij een (partial) update, maar wel mogen gezet worden bij een create
    * ``ResourceValidator`` - valideer dat een URL een bepaalde resource ontsluit
* Custom inspectors voor drf-yasg:
    * Support voor ``rest_framework_gis`` ``GeometryField``
    * SUpport voor ``django-extra-fields`` ``Base64FieldMixin``
    * URL-based related resource filtering (``django-filter`` support)
    * verzameling van mogelijke error-responses per operation
* Management command ``generate_swagger`` overloaded
    * neemt default versie mee en maakt server-informatie domein-agnostisch
    * optie om informatiemodel-resources naar markdown te renderen met backlinks
      naar gemmaonline.nl
* Support voor ISO 8601 durations
* Custom model fields:
    * ``RSINField``
    * ``BSNField``
    * ``LanguageField``
    * ``VertrouwelijkheidsAanduidingField``
    * ``DaysDurationField``
* Mocks voor de validators die netwerk IO hebben, eenvoudig via
  ``@override_settings`` toe te passen
* Test utilities
* Optionele notificaties applicatie:
    * ontvangen van webhook events
    * configureren en registreren van notificatiecomponent/webhooks


Installatie
===========

Benodigdheden
-------------

* Python 3.6 of hoger
* setuptools 30.3.0 of higher

Installeren
-----------

.. code-block:: bash

    pip install vng-api-common

Indien je de ``notifications`` app wil gebruiken, dan kan je extra dependencies
installeren via:

.. code-block:: bash

    pip install vng-api-common[notifications]

Gebruik
=======

Zie de referentie-implementaties voor `ZRC`_, `DRC`_, `BRC`_ en `ZTC`_.

.. _ZRC: https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent
.. _DRC: https://github.com/VNG-Realisatie/gemma-documentregistratiecomponent
.. _ZTC: https://github.com/VNG-Realisatie/gemma-zaaktypecatalogus
.. _BRC: https://github.com/VNG-Realisatie/gemma-besluitregistratiecomponent
