.. vng-api-common documentation master file, created by startproject.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to VNG-API-common's documentation!
=================================================

|build-status| |requirements| |coverage|

|python-versions| |django-versions| |pypi-version|

VNG-API-common implements generic tooling to implement and document RESTful
APIs in a Common Ground information architecture.

This package/tooling is used in the reference implementations in the ZGW-API
project, the reference lists and the Gemeentelijke Selectielijst.

VNG-API-common is a third party library for Django projects. It is based on
Django Rest Framework and drf-yasg for schema generation.

Features
========

* Custom field inspectors to generate the correct schema in the API spec
* Output to OAS 2 and OAS 3 format
* Custom model fields to encourage DRY
* Common validators for input validation
* Tooling for end-product unit-tests (mocks, custom clients)
* Optional support for notifications

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   notifications



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |build-status| image:: https://travis-ci.org/vng-Realisatie/vng-api-common.svg?branch=master
    :target: https://travis-ci.org/vng-Realisatie/vng-api-common

.. |requirements| image:: https://requires.io/github/vng-Realisatie/vng-api-common/requirements.svg?branch=master
    :target: https://requires.io/github/vng-Realisatie/vng-api-common/requirements/?branch=master
    :alt: Requirements status

.. |coverage| image:: https://codecov.io/gh/vng-Realisatie/vng-api-common/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/vng-Realisatie/vng-api-common
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/vng-api-common.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/vng-api-common.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/vng-api-common.svg
    :target: https://pypi.org/project/vng-api-common/
