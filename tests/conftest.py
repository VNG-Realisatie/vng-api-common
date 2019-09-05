import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from testapp.factories import PersonFactory

register(PersonFactory)


@pytest.fixture
def api_client():
    client = APIClient()
    return client
