==================
Obtaining a client
==================

Internally, the `APIClient`_ client is used to resolve remote API objects.


Public API
==========

Settings
--------

The setting ``CUSTOM_CLIENT_FETCHER`` is a string with the dotted path to a callable
taking a single ``url`` string argument. The callable should return a ready-to-use
client instance for that particular URL, or ``None`` if no suitable client can be
determined.

.. automodule:: vng_api_common.client
    :members:


.. _APIClient: https://ape-pie.readthedocs.io/en/stable/reference.html#apiclient-class
