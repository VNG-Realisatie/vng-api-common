.. _notifications:

=============
Notifications
=============

This library ships with support for notifications, in the form of view(set)
mixins and some simple configuration data models.

Installation
------------

To enable them, add:

.. code-block:: python

    ...,
    'django.contrib.sites',
    'vng_api_common.notifications',
    'solo',
    ...

to your ``INSTALLED_APPS`` setting.

Two additional settings are available:

* ``NOTIFICATIONS_KANAAL``: a string, the label of the 'kanaal' to register
  with the NC
* ``NOTIFICATIONS_DISABLED``: a boolean, default ``False``. Set to ``True`` to
  completely disable the sending of notifications.

Make sure to migrate your database:

.. code-block:: bash

    python manage.py migrate

Configuration
-------------

In the admin interface, open the notifications configuration and enter
the URL + credentials of the NC to use. You also need to add the credentials
in the ``vng_api_common`` APICredential section.

Make sure you also have the ``Sites`` set up correctly, as the domain
configured there is used to build the documentation URL.

After entering the configuration, you can register your 'kanaal' - this action
is idempotent:

.. code-block:: bash

    python manage.py register_kanaal

**Usage in code**

Define at least one ``Kanaal`` instance, typically this would go in
``api/kanalen.py``:

.. code-block:: python

    from vng_api_common.notifications.kanalen import Kanaal

    from zrc.datamodel.models import Zaak

    ZAKEN = Kanaal(
        'zaken',  # label of the channel/exchange
        main_resource=Zaak,  # main object for this channel/exchange
        kenmerken=(  # fields to include as 'kenmerken'
            'bronorganisatie',
            'zaaktype',
            'vertrouwelijkheidaanduiding'
        )
    )

To send notifications, add the mixins to the viewsets:

* ``vng_api_common.notifications.viewsets.NotificationCreateMixin``:
  send notifications for newly created objects

* ``vng_api_common.notifications.viewsets.NotificationUpdateMixin``:
  send notifications for (partial) upates to objects

* ``vng_api_common.notifications.viewsets.NotificationDestroyMixin``:
  send notifications for destroyed objects

* ``vng_api_common.notifications.viewsets.NotificationViewSetMixin``:
  a combination of all three mixins above

and define the attribute ``notifications_kanaal`` on the viewset:

.. code-block:: python

    from .kanalen import ZAKEN


    class ZaakViewSet(NotificationViewSetMixin, viewsets.ModelViewSet):
        ...
        notifications_kanaal = ZAKEN
