from ...models import JWTSecret
from ..kanalen import Kanaal
from ..utils import notification_documentation


def test_generate_docs():
    kanaal = Kanaal(label="dummy", main_resource=JWTSecret, kenmerken=("identifier",))

    result = notification_documentation(kanaal)

    expected = """### Notificaties

Deze API publiceert notificaties op het kanaal `dummy`.

**Main resource**

`jwtsecret`



**Kenmerken**

* `identifier`: Client ID to identify external API's and applications that access this API.

**Resources en acties**
"""
    assert result == expected
