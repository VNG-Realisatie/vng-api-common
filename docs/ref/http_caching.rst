============
HTTP Caching
============

HTTP caching is a mechanism that shines in RESTful APIs. A ``GET`` or ``HEAD``
response on a detail resource can be augmented with the ``ETag`` header, which
essentially is a "version" of a resource. Every modification of the resource
leads to a new version.

This can be leveraged in combination with the ``If-None-Match`` request header,
kwown as conditional requests.

The client includes the ``ETag`` value(s) in this header, and if the current
version of the resource has the same ``ETag`` value, then the server replies
with an ``HTTP 304`` response, indicating that the content has not changed.

This allows consumers to send less data over the wire without having to
perform extra requests if they keep resources in their own cache.

See the `ETag on MDN`_ documentation for the full specification.

Implementing conditional requests
=================================

Two actions are needed to implement this in API implementations:

Add the model mixin to save the ETag value
------------------------------------------

This enables us to perform fast lookups and avoid calculating the ETag value
over and over again. It happens automatically on ``save`` of a model instance.

.. code-block:: python
    :linenos:

    from vng_api_common.caching import ETagMixin


    class MyModel(ETagMixin, models.Model):
        pass

.. note:: If you're doing ``queryset.update`` or ``bulk_create`` operations,
   you need to take care of setting/calculating the value yourself.

Decorate the viewset
--------------------

Decorating the viewset retrieve ensures that the ``ETag`` header is set,
the conditional request handling (HTTP 200 vs. HTTP 304) is performed and the
extra methods/headers show up in the generated API schema.

.. code-block:: python
    :linenos:

    from rest_framework import viewsets
    from vng_api_common.caching import conditional_retrieve

    from .models import MyModel
    from .serializers import MyModelSerializer


    @conditional_retrieve()
    class MyModelViewSet(viewsets.ReadOnlyViewSet):
        queryset = MyModel.objects.all()
        serializer_class = MyModelSerializer


Public API
==========

.. automodule:: vng_api_common.caching
    :members:


.. _ETag on MDN: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
