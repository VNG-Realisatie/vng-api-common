==============
Change history
==============

2.0.0 (2024-11-22)
------------------

* upgrade to zgw-consumers 0.35.1
* remove zds-client dependency and replace with ``ape_pie.APIClient``
* upgrade to notifications-api-common>=0.3.0
* replace ``get_auth_headers`` with ``generate_jwt`` util

.. warning::

    If your project uses OAS test utilities, make sure to install them via ``commonground-api-common[testutils]``

.. warning::

    The ``APICredential`` class has been removed in favor of the ``Service`` model from zgw-consumers,
    a data migration is added to create ``Service`` instances from ``APICredential`` instances

.. warning::

    Several notifications related models (``NotificationsConfig`` and ``Subscription``) as well as
    the constants ``SCOPE_NOTIFICATIES_CONSUMEREN_LABEL`` and ``SCOPE_NOTIFICATIES_PUBLICEREN_LABEL`` have
    been removed, since they are defined in ``notifications-api-common`` and were a not deleted yet in ``commonground-api-common``

1.13.4 (2024-10-25)
-------------------

* Move AuthMiddleware to authorizations app, to avoid unnecessary migrations for projects that don't use ``vng_api_common.authorizations``

1.13.3 (2024-09-05)
-------------------

* Dropped support for Python 3.8 and Python 3.9
* [#33] Added dynamic pagination


1.13.2 (2024-07-05)
-------------------

* Added *identificatie* to ``UniekeIdentificatieValidator`` error message


1.13.1 (2024-05-28)
-------------------

* Marked notifications view scopes as private
* Added natural keys to authorization models


1.13.0 (2024-03-01)
-------------------

* Added support of Django 4.2
* Removed support of Python 3.7
* Added support of Python 3.11
