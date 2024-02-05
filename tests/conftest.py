"""
Define pytest configuration and setup.

The urls import is needed to make sure all urls/subclasses are registered
BEFORE fixtures run.
"""

from django.urls import clear_script_prefix, set_script_prefix

import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from testapp import urls  # noqa
from testapp.factories import GroupFactory, HobbyFactory, PersonFactory

register(PersonFactory, "person")
register(HobbyFactory)
register(GroupFactory)


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture
def script_path(request):
    set_script_prefix("/some-prefix")
    request.addfinalizer(clear_script_prefix)
