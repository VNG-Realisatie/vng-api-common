class Response:
    def __init__(self, status_code: int=200):
        self.status_code = status_code


def link_fetcher_404(url: str):
    return Response(status_code=404)


def link_fetcher_200(url: str):
    return Response(status_code=200)
