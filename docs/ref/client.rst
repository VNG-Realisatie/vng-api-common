==================
Obtaining a client
==================

Internally, the `APIClient`_ client is used to resolve remote API objects. To
allow the `APIClient`_ to correctly, e.g use correct credentials for authentication
, an `Service`_ instance is required with a matching `api_root`. This replaces
the previous mechanism to use `APICredentials` for this purpose. A data migration
will be performed to migrate `APICredentials` to the `Service`_ model.


.. _APIClient: https://ape-pie.readthedocs.io/en/stable/reference.html#apiclient-class
.. _Service: https://zgw-consumers.readthedocs.io/en/latest/models.html#zgw_consumers.models.Service
