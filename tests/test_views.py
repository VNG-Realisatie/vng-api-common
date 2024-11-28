from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

import pytest
import requests_mock
from notifications_api_common.models import NotificationsConfig
from rest_framework import status
from zgw_consumers.test.factories import ServiceFactory

from vng_api_common.authorizations.models import AuthorizationsConfig


@pytest.mark.django_db
def test_config_view(api_client):
    notifications_service = ServiceFactory(
        api_root="https://notificaties-api.vng.cloud/api/v1/"
    )
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = notifications_service
    notifications_config.save()

    authorizations_service = ServiceFactory(
        api_root="https://autorisaties-api.vng.cloud/api/v1/", client_id="foobar"
    )
    authorizations_config = AuthorizationsConfig.get_solo()
    authorizations_config.authorizations_api_service = authorizations_service
    authorizations_config.save()

    path = reverse("view-config")

    expected_request_notifications_url = f"{notifications_service.api_root}kanaal"

    expected_request_authorizations_url = (
        f"{authorizations_service.api_root}applicaties?clientIds=foobar"
    )

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get(expected_request_notifications_url, status_code=200)
        request_mocker.get(expected_request_authorizations_url, status_code=200)

        response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK

    assert request_mocker.call_count == 2

    authorization_request = request_mocker.request_history[0]
    assert authorization_request.url == expected_request_authorizations_url

    notifications_request = request_mocker.request_history[1]
    assert notifications_request.url == expected_request_notifications_url


@pytest.mark.django_db
def test_config_view_missing_notifications_service(api_client):
    """
    regression test for https://github.com/open-zaak/open-notificaties/issues/119
    """
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = None
    notifications_config.save()

    authorizations_service = ServiceFactory(
        api_root="https://autorisaties-api.vng.cloud/api/v1/", client_id="foobar"
    )
    authorizations_config = AuthorizationsConfig.get_solo()
    authorizations_config.authorizations_api_service = authorizations_service
    authorizations_config.save()

    path = reverse("view-config")

    expected_request_authorizations_url = (
        f"{authorizations_service.api_root}applicaties?clientIds=foobar"
    )

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get(expected_request_authorizations_url, status_code=200)

        response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK

    assert request_mocker.call_count == 1

    authorization_request = request_mocker.request_history[0]
    assert authorization_request.url == expected_request_authorizations_url


@pytest.mark.django_db
def test_config_view_notifications_error_response(api_client):
    notifications_service = ServiceFactory(
        api_root="https://notificaties-api.vng.cloud/api/v1/"
    )
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = notifications_service
    notifications_config.save()

    authorizations_service = ServiceFactory(
        api_root="https://autorisaties-api.vng.cloud/api/v1/", client_id="foobar"
    )
    authorizations_config = AuthorizationsConfig.get_solo()
    authorizations_config.authorizations_api_service = authorizations_service
    authorizations_config.save()

    path = reverse("view-config")

    expected_request_notifications_url = f"{notifications_service.api_root}kanaal"

    expected_request_authorizations_url = (
        f"{authorizations_service.api_root}applicaties?clientIds=foobar"
    )

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get(expected_request_notifications_url, status_code=403)
        request_mocker.get(expected_request_authorizations_url, status_code=200)

        response: TemplateResponse = api_client.get(path)

    response_content = response.content.decode("utf-8")

    assert response.status_code == status.HTTP_200_OK
    assert (
        _("Cannot retrieve kanalen: HTTP {status_code}").format(status_code=403)
        in response_content
    )

    assert request_mocker.call_count == 2

    authorization_request = request_mocker.request_history[0]
    assert authorization_request.url == expected_request_authorizations_url

    notifications_request = request_mocker.request_history[1]
    assert notifications_request.url == expected_request_notifications_url


@pytest.mark.django_db
def test_config_view_missing_authorizations_service(api_client):
    notifications_service = ServiceFactory(
        api_root="https://notificaties-api.vng.cloud/api/v1/"
    )
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = notifications_service
    notifications_config.save()

    authorizations_config = AuthorizationsConfig.get_solo()
    authorizations_config.authorizations_api_service = None
    authorizations_config.save()

    path = reverse("view-config")

    expected_request_notifications_url = f"{notifications_service.api_root}kanaal"

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get(expected_request_notifications_url, status_code=200)

        response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK

    assert request_mocker.call_count == 1

    notifications_request = request_mocker.request_history[0]
    assert notifications_request.url == expected_request_notifications_url


@pytest.mark.django_db
def test_config_view_authorizations_error_response(api_client):
    notifications_service = ServiceFactory(
        api_root="https://notificaties-api.vng.cloud/api/v1/"
    )
    notifications_config = NotificationsConfig.get_solo()
    notifications_config.notifications_api_service = notifications_service
    notifications_config.save()

    authorizations_service = ServiceFactory(
        api_root="https://autorisaties-api.vng.cloud/api/v1/", client_id="foobar"
    )
    authorizations_config = AuthorizationsConfig.get_solo()
    authorizations_config.authorizations_api_service = authorizations_service
    authorizations_config.save()

    path = reverse("view-config")

    expected_request_notifications_url = f"{notifications_service.api_root}kanaal"

    expected_request_authorizations_url = (
        f"{authorizations_service.api_root}applicaties?clientIds=foobar"
    )

    with requests_mock.Mocker() as request_mocker:
        request_mocker.get(expected_request_notifications_url, status_code=200)
        request_mocker.get(expected_request_authorizations_url, status_code=403)

        response: TemplateResponse = api_client.get(path)

    response_content = response.content.decode("utf-8")

    assert response.status_code == status.HTTP_200_OK
    assert "Could not connect with AC" in response_content

    assert request_mocker.call_count == 2

    authorization_request = request_mocker.request_history[0]
    assert authorization_request.url == expected_request_authorizations_url

    notifications_request = request_mocker.request_history[1]
    assert notifications_request.url == expected_request_notifications_url
