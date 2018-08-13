====================================
ZDS-Schema - Schema-generatietooling
====================================

ZDS-Schema voorziet een generieke API schema-generatiestrategie die gedeeld
wordt tussen verschillende componenten betrokken in zaakgericht werken.

.. contents::

.. section-numbering::

Features
========

* Centraal beheer van cosntanten die de verschillende componenten overstijgen
* GeoJSON OpenAPI definities
* Support voor Geo CRS negotation
* Ingebouwde support voor nested viewsets met declaratievere syntax voor
  registratie
* Vaak voorkomende validators:
    * RSIN/BSN validator
    * Numerieke waarde validator
    * Niet-negatieve waarde validator
    * Alfanumerieke waarde (zonder diacritics)
* Custom inspectors voor drf-yasg:
    * Support voor ``rest_framework_gis`` ``GeometryField``
    * URL-based related resource filtering (``django-filter`` support)
* Management command ``generate_swagger`` overloaded om default versie mee te
  nemen en server-informatie domein-agnostisch te maken
* Support voor ISO 8601 durations
* Custom model fields:
    * ``RSINField``
    * ``BSNField``
    * ``LanguageField``
    * ``VertrouwelijkheidsAanduidingField``
    * ``DaysDurationField``


Installatie
===========

Benodigdheden
-------------

* Python 3.6 of hoger
* setuptools 30.3.0 of higher

Installeren
-----------

.. code-block:: bash

    pip install -e git+https://github.com/maykinmedia/gemma-zaken-common.git@master#egg=zds_schema

Gebruik
=======

Zie de referentie-implementaties voor `ZRC`_, `DRC`_ en `ZTC`_.

.. _ZRC: https://github.com/VNG-Realisatie/gemma-zaakregistratiecomponent
.. _DRC: https://github.com/VNG-Realisatie/gemma-documentregistratiecomponent
.. _ZTC: https://github.com/VNG-Realisatie/gemma-zaaktypecatalogus
