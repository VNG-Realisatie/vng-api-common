import logging
from typing import Any, Dict, Iterable, List, Optional

from django.conf import settings
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils.translation import gettext as _

import jwt
from djangorestframework_camel_case.util import underscoreize
from requests import RequestException
from rest_framework.exceptions import PermissionDenied

from vng_api_common.client import ClientError, to_internal_data
from vng_api_common.constants import VertrouwelijkheidsAanduiding

from ..models import JWTSecret
from ..utils import get_uuid_from_path
from .models import Applicatie, AuthorizationsConfig, Autorisatie
from .serializers import ApplicatieUuidSerializer

logger = logging.getLogger(__name__)


class JWTAuth:
    def __init__(self, encoded: Optional[str] = None):
        self.encoded = encoded

    @property
    def applicaties(self) -> Iterable[Applicatie]:
        if self.client_id is None:
            return []

        applicaties = self._get_auth()

        if not applicaties:
            auth_data = self._request_auth()
            applicaties = self._save_auth(auth_data)

        return applicaties

    @property
    def autorisaties(self) -> models.QuerySet:
        """
        Retrieve all authorizations relevant to this component.
        """
        app_ids = [app.id for app in self.applicaties]
        config = AuthorizationsConfig.get_solo()
        return Autorisatie.objects.filter(
            applicatie_id__in=app_ids, component=config.component
        )

    def _request_auth(self) -> list:
        client = AuthorizationsConfig.get_client()

        if not client:
            logger.warning("Authorization component can't be accessed")
            return []

        try:
            response = client.get("applicaties", params={"clientIds": self.client_id})

            data = to_internal_data(response)
        except RequestException:
            logger.warning("Authorization component can't be accessed")
            return []
        except ClientError as exc:
            response = exc.args[0]
            # friendly debug - hint at where the problem is located
            if response["status"] == 403 and response["code"] == "not_authenticated":
                detail = _(
                    "Component could not authenticate against the AC - "
                    "authorizations could not be retrieved"
                )
                raise PermissionDenied(detail=detail, code="not_authenticated_for_ac")
            logger.warning("Authorization component can't be accessed")
            return []

        return underscoreize(data["results"])

    def _get_auth(self):
        return Applicatie.objects.filter(client_ids__contains=[self.client_id])

    @transaction.atomic
    def _save_auth(self, auth_data):
        applicaties = []

        for applicatie_data in auth_data:
            applicatie_serializer = ApplicatieUuidSerializer(data=applicatie_data)
            uuid = get_uuid_from_path(applicatie_data["url"])
            applicatie_data["uuid"] = uuid
            applicatie_serializer.is_valid()
            applicaties.append(applicatie_serializer.save())

        return applicaties

    @property
    def payload(self) -> Optional[Dict[str, Any]]:
        if self.encoded is None:
            return None

        if not hasattr(self, "_payload"):
            # decode the JWT and validate it

            # jwt check
            try:
                payload = jwt.decode(
                    self.encoded,
                    algorithms=["HS256"],
                    options={"verify_signature": False},
                    leeway=settings.JWT_LEEWAY,
                )
            except jwt.DecodeError:
                logger.info("Invalid JWT encountered")
                raise PermissionDenied(
                    _(
                        "JWT could not be decoded. Possibly you made a copy-paste mistake."
                    ),
                    code="jwt-decode-error",
                )

            # get client_id
            try:
                client_id = payload["client_id"]
            except KeyError:
                raise PermissionDenied(
                    "Client identifier is niet aanwezig in JWT",
                    code="missing-client-identifier",
                )

            # find client_id in DB and retrieve its secret
            try:
                jwt_secret = JWTSecret.objects.exclude(secret="").get(
                    identifier=client_id
                )
            except JWTSecret.DoesNotExist:
                raise PermissionDenied(
                    "Client identifier bestaat niet", code="invalid-client-identifier"
                )
            else:
                key = jwt_secret.secret

            # check signature of the token
            try:
                payload = jwt.decode(
                    self.encoded,
                    key,
                    algorithms=["HS256"],
                    leeway=settings.JWT_LEEWAY,
                )
            except jwt.InvalidSignatureError:
                logger.exception("Invalid signature - possible payload tampering?")
                raise PermissionDenied(
                    "Client credentials zijn niet geldig", code="invalid-jwt-signature"
                )

            self._payload = payload

        return self._payload

    @property
    def client_id(self) -> Optional[str]:
        if not self.payload:
            return None
        return self.payload["client_id"]

    def filter_vertrouwelijkheidaanduiding(self, base: QuerySet, value) -> QuerySet:
        if value is None:
            return base

        order_provided = VertrouwelijkheidsAanduiding.get_choice_order(value)
        order_case = VertrouwelijkheidsAanduiding.get_order_expression(
            "max_vertrouwelijkheidaanduiding"
        )

        # In this case we are filtering Autorisatie model to look for auth which meets our needs.
        # Therefore we're only considering authorizations here that have a max_vertrouwelijkheidaanduiding
        # bigger or equal than what we're checking for the object.
        # In cases when we are filtering data objects (Zaak, InformatieObject etc) it's the other way around

        return base.annotate(max_vertr=order_case).filter(max_vertr__gte=order_provided)

    def filter_default(self, base: QuerySet, name, value) -> QuerySet:
        if value is None:
            return base

        return base.filter(**{name: value})

    def has_auth(
        self, scopes: List[str], component: Optional[str] = None, **fields
    ) -> bool:
        if scopes is None:
            return False

        scopes_provided = set()
        config = AuthorizationsConfig.get_solo()
        if component is None:
            component = config.component

        for applicatie in self.applicaties:
            # allow everything
            if applicatie.heeft_alle_autorisaties is True:
                return True

            autorisaties = applicatie.autorisaties.filter(component=component)

            # filter on all additional components
            for field_name, field_value in fields.items():
                if hasattr(self, f"filter_{field_name}"):
                    autorisaties = getattr(self, f"filter_{field_name}")(
                        autorisaties, field_value
                    )
                else:
                    autorisaties = self.filter_default(
                        autorisaties, field_name, field_value
                    )

            for autorisatie in autorisaties:
                scopes_provided.update(autorisatie.scopes)

        return scopes.is_contained_in(list(scopes_provided))


class AuthMiddleware:
    header = "HTTP_AUTHORIZATION"
    auth_type = "Bearer"

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.extract_jwt_payload(request)
        return self.get_response(request) if self.get_response else None

    def extract_jwt_payload(self, request):
        authorization = request.META.get(self.header, "")
        prefix = f"{self.auth_type} "
        if authorization.startswith(prefix):
            # grab the actual token
            encoded = authorization[len(prefix) :]
        else:
            encoded = None

        request.jwt_auth = JWTAuth(encoded)
