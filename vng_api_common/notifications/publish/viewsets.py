import logging
from typing import Dict, List, Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone

from djangorestframework_camel_case.util import camelize
from rest_framework.permissions import SAFE_METHODS
from rest_framework.routers import SimpleRouter
from zds_client import ClientError

from ...utils import get_resource_for_path
from ..api.serializers import NotificatieSerializer
from ..kanalen import Kanaal
from ..models import NotificationsConfig

logger = logging.getLogger(__name__)


class NotificationMixinBase(type):

    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)

        kanaal = attrs.get('notifications_kanaal')
        if kanaal is None:
            return new_cls

        relevant_bases = [base for base in bases if issubclass(base, NotificationMixin)]
        resource = new_cls.queryset.model._meta.model_name
        # use the router to figure out which actions are available
        router = SimpleRouter()
        for route in router.get_routes(new_cls):
            for method, action in route.mapping.items():

                if method.upper() in SAFE_METHODS:
                    continue

                # check if the action is actually provided by one of the mixins
                if not any(hasattr(base, action) for base in relevant_bases):
                    continue

                kanaal.usage[resource].append(action)

        return new_cls


class NotificationMixin(metaclass=NotificationMixinBase):
    notifications_kanaal = None  # must be set be subclasses

    def get_kanaal(self):
        if not self.notifications_kanaal:
            raise ImproperlyConfigured(
                "'%s' should either include a `notifications_kanaal` "
                "attribute, or override the `get_kanaal()` method."
                % self.__class__.__name__
            )
        return self.notifications_kanaal

    def construct_message(self, data: dict, instance: models.Model = None) -> dict:
        """
        Construct the message to send to the notification component.

        Using the response data from the view/action, we introspect this data
        to send the appropriate response. By convention, every resource
        includes its own absolute url in the 'url' key - we can use this to
        look up the object it points to. By convention, relations use the name
        of the resource, so for sub-resources we can use this to get a
        reference back to the main resource.
        """
        kanaal = self.get_kanaal()
        assert isinstance(kanaal, Kanaal), "`kanaal` should be a `Kanaal` instance"

        model = self.get_queryset().model

        # NOTE: possibly this may need to become its own, overrideable method
        if model is kanaal.main_resource:
            # look up the object in the database from its absolute URL
            resource_path = urlparse(data['url']).path
            resource = instance or get_resource_for_path(resource_path)

            main_object = resource
            main_object_url = data['url']
        else:
            # using the main resource name, look up what the URL to this
            # object is/should be, and fetch the object from the db
            main_object_url = data[kanaal.main_resource._meta.model_name]
            main_object_path = urlparse(main_object_url).path
            main_object = get_resource_for_path(main_object_path)

        message_data = {
            'kanaal': kanaal.label,
            'hoofd_object': main_object_url,
            'resource': model._meta.model_name,
            'resource_url': data['url'],
            'actie': self.action,
            'aanmaakdatum': timezone.now(),
            # each channel knows which kenmerken it has, so delegate this
            'kenmerken': kanaal.get_kenmerken(main_object),
        }

        # let the serializer & render machinery shape the data the way it
        # should be, suitable for JSON in/output
        serializer = NotificatieSerializer(instance=message_data)
        return camelize(serializer.data)

    def notify(self,
               status_code: int,
               data: Union[List, Dict], instance: models.Model = None) -> Union[None, List, Dict]:
        if settings.NOTIFICATIONS_DISABLED:
            return

        # do nothing unless we have a 'success' status code - early exit here
        if not 200 <= status_code < 300:
            logger.info("Not notifying, status code '%s' does not represent success.", status_code)
            return

        # build the content of the notification
        message = self.construct_message(data, instance=instance)

        # build the client from the singleton config. This will raise an
        # exception if the config is not complete. We want this to hard-fail!
        client = NotificationsConfig.get_client()
        try:
            response = client.create('notificaties', message)
        # any unexpected errors should show up in error-monitoring, so we only
        # catch ClientError exceptions
        except ClientError as exc:
            logger.warning("Could not deliver message to %s", client.base_url, exc_info=True)

        return response


class NotificationCreateMixin(NotificationMixin):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.notify(response.status_code, response.data)
        return response


class NotificationUpdateMixin(NotificationMixin):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.notify(response.status_code, response.data)
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        self.notify(response.status_code, response.data)
        return response


class NotificationDestroyMixin(NotificationMixin):
    def destroy(self, request, *args, **kwargs):
        # get data via serializer
        instance = self.get_object()
        data = self.get_serializer(instance).data

        response = super().destroy(request, *args, **kwargs)
        self.notify(response.status_code, data, instance=instance)
        return response


class NotificationViewSetMixin(NotificationCreateMixin,
                               NotificationUpdateMixin,
                               NotificationDestroyMixin):
    pass
