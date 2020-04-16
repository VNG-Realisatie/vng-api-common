from django.urls import clear_script_prefix, set_script_prefix

import pytest


@pytest.fixture
def script_path(request):
    set_script_prefix("/some-prefix")
    request.addfinalizer(clear_script_prefix)
