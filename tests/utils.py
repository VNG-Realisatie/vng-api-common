import time

import jwt

JWT_ALG = "HS256"


def get_auth_headers(
    client_id: str,
    client_secret: str,
    user_id: str = "",
    user_representation: str = "",
    **claims,
) -> dict:
    payload = {
        # standard claims
        "iss": client_id,
        "iat": int(time.time()),
        # custom claims
        "client_id": client_id,
        "user_id": user_id,
        "user_representation": user_representation,
        **claims,
    }

    encoded = jwt.encode(payload, client_secret, algorithm=JWT_ALG)

    return {"Authorization": "Bearer {encoded}".format(encoded=encoded)}
