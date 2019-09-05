"""
Define pytest configuration and setup.

The urls import is needed to make sure all urls/subclasses are registered
BEFORE fixtures run.
"""
import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from testapp import urls  # noqa
from testapp.factories import PersonFactory

register(PersonFactory)


@pytest.fixture
def api_client():
    client = APIClient()
    return client
