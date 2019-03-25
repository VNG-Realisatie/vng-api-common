import re
from urllib.parse import urlparse

from zds_client.client import UUID_PATTERN


class Response:
    def __init__(self, status_code: int=200):
        self.status_code = status_code

    def json(self) -> dict:
        return {}


def link_fetcher_404(url: str, *args, **kwargs):
    return Response(status_code=404)


def link_fetcher_200(url: str, *args, **kwargs):
    return Response(status_code=200)


class MockClient:
    data = {}

    @classmethod
    def from_url(cls, detail_url: str):
        clients = {
            'ztc': ZTCMockClient,
            'drc': DRCMockClient,
            'notificaties': NotifMockClient
        }

        parsed_url = urlparse(detail_url)

        if ':' in parsed_url.netloc:
            host, port = parsed_url.netloc.split(':')
        else:
            host = parsed_url.netloc

        # Try mock client based on host.
        if host in clients:
            return clients[host]()

        # Try mock client based first element of the path.
        first_path_element = parsed_url.path.strip('/').split('/', 1)[0]
        if first_path_element in clients:
            return clients[first_path_element]()

        # Try mock client based on last element of the path - for notifications
        last_path_element = parsed_url.path.split('/')[-1]
        if last_path_element in clients:
            return clients[last_path_element]()

        raise ValueError('Cannot determine service based on url: %s', detail_url)

    def request(self, path: str, operation: str, method='GET', **kwargs):
        bits = path.rsplit('/', 2)

        # Match UUIDs and simple numbers that are most likely used for testing.
        if re.match(r'^({}|[0-9]+)$'.format(UUID_PATTERN), bits[-1]):
            resource = bits[-2]
            uuid = bits[-1]
        else:
            resource = bits[-1]
            uuid = None

        # Should the mock client really consult an OAS to figure out the
        # operation? Workaround for now is to strip off plural forms ("n", "s",
        # "sen").
        if resource not in self.data:
            if resource[0:-1] in self.data:
                resource = resource[0:-1]
            elif resource[0:-3] in self.data:
                resource = resource[0:-3]

        if method == 'POST' and not uuid:
            return self.create(resource)

        if method == 'GET' and not uuid:
            return self.list(resource)

        return self.retrieve(resource, uuid=uuid)

    def list(self, resource: str, *args, **kwargs):
        return self.data.get(resource, [])

    def retrieve(self, resource: str, *args, **kwargs):
        try:
            index = int(kwargs.get('uuid', 1)) - 1
        except ValueError:
            index = 0

        # result = copy.deepcopy(self.data.get(resource)[index])
        # result['url'] = result['url'].format(**kwargs)
        return self.data.get(resource)[index]

    def create(self, resource: str, *args, **kwargs):
        return self.data.get(resource, {})


class ZTCMockClient(MockClient):

    data = {
        'statustype': [{
            'url': 'https://ztc/api/v1/catalogussen/{catalogus_uuid}/zaaktypen/{zaaktype_uuid}/statustypen/{uuid}',
            'volgnummer': 1,
            'isEindstatus': False,
        }, {
            'url': 'https://ztc/api/v1/catalogussen/{catalogus_uuid}/zaaktypen/{zaaktype_uuid}/statustypen/{uuid}',
            'volgnummer': 2,
            'isEindstatus': True,
        }],
    }


class DRCMockClient(MockClient):

    data = {
        'objectinformatieobject': [{
            'url': 'https://mock/objectinformatieobjecten/1234',
            'informatieobject': '',
            'object': '',
            'objectType': '',
            'titel': '',
            'beschrijving': '',
            'registratiedatum': '',
        }]
    }


class ObjectInformatieObjectClient(DRCMockClient):
    """
    Kept for backwards compatability.
    """
    @classmethod
    def from_url(cls, *args, **kwargs):
        return cls()

    def list(self, resource, *args, **kwargs):
        assert resource == 'objectinformatieobject'
        return self.data[resource]


class NotifMockClient(MockClient):
    """
    for sending notifications
    """
    data = {
        'notificaties': {}
    }
