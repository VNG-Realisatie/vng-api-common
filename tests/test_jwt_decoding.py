from datetime import datetime

import jwt
import pytest
from freezegun import freeze_time
from jwt import ImmatureSignatureError

from vng_api_common.middleware import JWTAuth
from vng_api_common.models import JWTSecret


@pytest.mark.django_db
def test_jwt_decode_ok():
    secret = "secret"
    JWTSecret.objects.create(identifier="client", secret=secret)
    token = jwt.encode({"client_id": "client"}, secret, algorithm="HS256")

    auth = JWTAuth(token)

    payload = auth.payload
    assert auth.client_id == "client"
    assert payload == {"client_id": "client"}


@pytest.mark.django_db
@freeze_time("2021-08-23T14:20:00")
def test_nbf_validated():
    JWTSecret.objects.create(identifier="client", secret="secret")
    payload = {
        "client_id": "client",
        "nbf": int(datetime.now().timestamp())
        + 1,  # 1 second "later" than current time
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    auth = JWTAuth(token)

    with pytest.raises(ImmatureSignatureError):
        auth.payload


@pytest.mark.django_db
@freeze_time("2021-08-23T14:20:00")
def test_nbf_validated_with_leeway(settings):
    settings.JWT_LEEWAY = 3
    JWTSecret.objects.create(identifier="client", secret="secret")
    payload = {
        "client_id": "client",
        "nbf": int(datetime.now().timestamp())
        + 1,  # 1 second "later" than current time
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    auth = JWTAuth(token)

    assert auth.payload == payload
