def generate_jwt(client_id, secret, user_id, user_representation):
    from zgw_consumers.client import ZGWAuth

    class FakeService:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    auth = ZGWAuth(
        service=FakeService(  # type: ignore
            client_id=client_id,
            secret=secret,
            user_id=user_id,
            user_representation=user_representation,
        )
    )
    return f"Bearer {auth._token}"
