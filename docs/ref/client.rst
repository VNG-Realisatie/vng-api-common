==================
Obtaining a client
==================

Internally, `zds-client`_ is used to resolve remote API objects where the API is
documented using OpenAPI 3 specifications.

Subclasses of the base ``Client`` class can also be used, in a pluggable fashion. By
default, the base class is used in combination with
:class:`vng_api_common.models.APICredential`.


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


.. _zds-client: https://pypi.org/project/gemma-zds-client/
