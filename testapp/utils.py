# Custom function to get client for ClientConfig models
def get_client(url):
    return "testclient"


# Custom function to get client with auth for ClientConfig models
def get_client_with_auth(url):
    class TestClient:
        auth = None

    return TestClient
