import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.test import APIRequestFactory

from testapp.viewsets import GroupViewSet as _GroupViewSet
from vng_api_common.viewsets import CheckQueryParamsMixin


class CustomOrderingFilter(OrderingFilter):
    ordering_param = "custom_ordering"


class GroupViewSet(CheckQueryParamsMixin, _GroupViewSet):
    filter_backends = (OrderingFilter,)


def test_check_query_params_regular_ordering_filter():
    factory = APIRequestFactory()
    request = factory.get("/foo", format="json")
    request.query_params = {"ordering": "datum"}

    GroupViewSet()._check_query_params(request)


def test_check_query_params_subclassed_ordering_filter():
    GroupViewSet.filter_backends = (CustomOrderingFilter,)

    factory = APIRequestFactory()
    request = factory.get("/foo", format="json")

    # Should be possible to use custom ordering_param name
    request.query_params = {"custom_ordering": "datum"}

    GroupViewSet()._check_query_params(request)


def test_check_query_params_not_allowed():
    GroupViewSet.filter_backends = (CustomOrderingFilter,)

    factory = APIRequestFactory()
    request = factory.get("/foo", format="json")

    # Incorrect parameters should still be blocked
    request.query_params = {"incorrect_param": "datum"}

    with pytest.raises(ValidationError):
        GroupViewSet()._check_query_params(request)
