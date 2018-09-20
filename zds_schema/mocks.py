class Response:
    def __init__(self, status_code: int=200):
        self.status_code = status_code


def link_fetcher_404(url: str, *args, **kwargs):
    return Response(status_code=404)


def link_fetcher_200(url: str, *args, **kwargs):
    return Response(status_code=200)


class ObjectInformatieObjectClient:

    @classmethod
    def from_url(cls, *args, **kwargs):
        return cls()

    def list(self, resource, *args, **kwargs):
        assert resource == 'objectinformatieobject'
        return [{
            'url': 'https://mock/objectinformatieobjecten/1234',
            'informatieobject': '',
            'object': '',
            'objectType': '',
            'titel': '',
            'beschrijving': '',
            'registratiedatum': '',
        }]
