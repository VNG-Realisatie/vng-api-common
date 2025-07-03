==========================================
VNG-API-common - Tooling voor RESTful APIs
==========================================

|build-status| |code-quality| |coverage| |docs| |black|

|python-versions| |django-versions| |pypi-version|

VNG-API-common biedt generieke implementaties en tooling voor RESTful APIs
in een Common Ground gegevenslandschap.

De tooling wordt o.a. gebruikt in de referentie-implementaties van componenten
voor zaakgericht werken, maar ook in VNG-APIs voor referentielijsten en de
Gemeentelijke Selectielijst.

Zie de uitgebreide `documentatie`_ voor de features en het gebruik.

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

.. |build-status| image:: https://github.com/VNG-Realisatie/vng-api-common/workflows/ci-build/badge.svg
    :alt: Build status
    :target: https://github.com/VNG-Realisatie/vng-api-common/actions?query=workflow%3A%22ci-build%22

.. |code-quality| image:: https://github.com/VNG-Realisatie/vng-api-common/workflows/Code%20quality%20checks/badge.svg
     :alt: Code quality checks
     :target: https://github.com/VNG-Realisatie/vng-api-common/actions?query=workflow%3A%22Code+quality+checks%22

.. |coverage| image:: https://codecov.io/gh/VNG-Realisatie/vng-api-common/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/VNG-Realisatie/vng-api-common
    :alt: Coverage status

.. |docs| image:: https://readthedocs.org/projects/vng-api-common/badge/?version=latest
    :target: https://vng-api-common.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/vng-api-common.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/vng-api-common.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/vng-api-common.svg
    :target: https://pypi.org/project/vng-api-common/

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. _documentatie: https://vng-api-common.readthedocs.io/en/latest/?badge=latest
