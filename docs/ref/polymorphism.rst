============
Polymorphism
============

.. epigraph::
    Polymorphism describes a pattern in object oriented programming in which
    classes have different functionality while sharing a common interface.

    -- Someone on Stack Overflow

Sometimes data exposed via the API has a different shape, depending on the
value of a field that's common to all possible shapes.

This module adds support for polymorphic serializing and deserializing of this
data.

You use it by defining a base serializer for the shared fields (at least one,
used as discriminator field), and map the values of the discriminator to the
additional fields that need to be displayed.

A field inspector is included to output is correctly into an OAS 2.0 schema.

Public API
==========

.. automodule:: vng_api_common.polymorphism
    :members:
