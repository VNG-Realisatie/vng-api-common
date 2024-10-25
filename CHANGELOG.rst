==============
Change history
==============

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
