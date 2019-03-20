import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.module_loading import import_string
from django.utils.timezone import now

from vng_api_common.models import APICredential


class NotificationMixin:
    kenmerken = None
    hoofd = None

    def get_nc_url(self):
        if not hasattr(settings, 'NC_URL'):
            raise ImproperlyConfigured(
                "For sending notifications settings should include "
                "NC_URL parameter"
            )
        return settings.NC_URL

    def get_kanaal(self):
        if not hasattr(settings, 'KANAAL'):
            raise ImproperlyConfigured(
                "For sending notifications settings should include "
                "KANAAL parameter"
            )
        return settings.KANAAL

    def get_hoofd(self):
        if self.hoofd is not None:
            return self.hoofd
        if not hasattr(settings, 'HOOFD'):
            raise ImproperlyConfigured(
                "For sending notifications settings or viewset attributes "
                "should include HOOFD parameter"
            )
        return settings.HOOFD

    def get_kenmerken(self):
        """
        Return a `list` of `dict` representing all the kenmerken.
        Each `APIView` or `ViewSet` should implement this.
        """
        assert self.kenmerken is not None, (
            "{} should either include a `kenmerken` attribute, "
            "or override the `get_kenmerken()` method.".format(self.__class__.__name__)
        )
        return self.kenmerken

    def construct_message(self, data, *args, **kwargs):
        msg = {
            "kanaal": self.get_kanaal(),
            "resourceUrl": data.get('url', None),
            "resource": kwargs['resource'],
            "actie": kwargs['action'],
            "aanmaakdatum": now(),
            "kenmerken": self.get_kenmerken()
        }

        hoofd = self.get_hoofd()
        if kwargs['resource'] == hoofd:
            msg["hoofdObject"] = data.get('url', None)
        else:
            msg["hoofdObject"] = data.get(hoofd, None)

        return json.dumps(msg, cls=DjangoJSONEncoder)

    def notify(self, status_code, data):
        url = self.get_nc_url()
        response = None

        if status_code >= 200 and status_code < 300:
            Client = import_string(settings.ZDS_CLIENT_CLASS)
            client = Client.from_url(url)
            client.auth = APICredential.get_auth(
                url,
                scopes=['notificaties.scopes.publiceren']
            )

            msg = self.construct_message(data, action=self.action, resource=self.basename)

            response = client.request(
                url, 'notificaties',
                method='POST',
                data=msg,
                expected_status=201
            )
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


class NotificationDestroyMixin(NotificationMixin):
    def destroy(self, request, *args, **kwargs):
        # get data via serializer
        data = self.get_serializer(self.get_object()).data

        response = super().destroy(request, *args, **kwargs)
        self.notify(response.status_code, data)
        return response


class NotificationViewSetMixin(NotificationCreateMixin,
                               NotificationUpdateMixin,
                               NotificationDestroyMixin):
    pass
