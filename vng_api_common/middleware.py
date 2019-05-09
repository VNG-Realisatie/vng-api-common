# https://pyjwt.readthedocs.io/en/latest/usage.html#reading-headers-without-validation
# -> we can put the organization/service in the headers itself
import logging
from typing import List, Union

from django.conf import settings
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

import jwt
from djangorestframework_camel_case.util import underscoreize
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from zds_client.client import ClientError

from .authorizations.models import (
    Applicatie, AuthorizationsConfig, Autorisatie
)
from .authorizations.serializers import ApplicatieUuidSerializer
from .constants import VERSION_HEADER, VertrouwelijkheidsAanduiding
from .models import JWTSecret
from .scopes import Scope
from .utils import get_uuid_from_path

logger = logging.getLogger(__name__)

EMPTY_PAYLOAD = {
    'scopes': [],
    'zaaktypes': [],
}


class JWTPayload:

    def __init__(self, encoded: str=None):
        self.encoded = encoded

    def __repr__(self):
        return "<%s: payload=%r>" % (self.__class__.__name__, self.payload)

    def __getitem__(self, key):
        return self.payload[key]

    def get(self, attr, *args, **kwargs):
        return self.payload.get(attr, *args, **kwargs)

    @cached_property
    def payload(self) -> dict:
        if self.encoded is None:
            return EMPTY_PAYLOAD

        try:
            header = jwt.get_unverified_header(self.encoded)
        except jwt.DecodeError:
            logger.info("Invalid JWT encountered")
            raise PermissionDenied(
                _('JWT could not be decoded. Possibly you made a copy-paste mistake.'),
                code='jwt-decode-error'
            )

        try:
            jwt_secret = JWTSecret.objects.get(identifier=header['client_identifier'])
        except JWTSecret.DoesNotExist:
            raise PermissionDenied(
                'Client identifier bestaat niet',
                code='invalid-client-identifier'
            )
        except KeyError:
            raise PermissionDenied(
                'Client identifier is niet aanwezig in JWT',
                code='missing-client-identifier'
            )
        else:
            key = jwt_secret.secret

        # the jwt package does verification against tampering (TODO: unit test)
        try:
            payload = jwt.decode(self.encoded, key, algorithms='HS256')
        except jwt.InvalidSignatureError as exc:
            logger.exception("Invalid signature - possible payload tampering?")
            raise PermissionDenied(
                'Client credentials zijn niet geldig',
                code='invalid-jwt-signature'
            )

        res = payload.get('zds', EMPTY_PAYLOAD)
        res['client_id'] = header['client_identifier']

        return res

    def has_scopes(self, scopes: Union[Scope, None]) -> bool:
        """
        Check whether all of the expected scopes are present or not.
        """
        if scopes is None:
            # TODO: should block instead of allow it - we'll gradually introduce this
            return True

        scopes_provided = self.payload.get('scopes', [])
        logger.debug("Scopes provided are: %s", scopes)
        # simple form - needs a more complex setup if a scope 'bundles'
        # other scopes
        return scopes.is_contained_in(scopes_provided)


class JWTAuth:
    def __init__(self, encoded: str = None):
        self.encoded = encoded

    @property
    def applicaties(self) -> Union[list, None]:
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
        return (
            Autorisatie.objects
            .filter(
                applicatie_id__in=app_ids,
                component=config.component
            )
        )

    def _request_auth(self) -> list:
        client = AuthorizationsConfig.get_client()
        try:
            response = client.list(
                'applicatie',
                query_params={'client_ids': self.client_id}
            )
        except ClientError as exc:
            response = exc.args[0]
            # friendly debug - hint at where the problem is located
            if response['status'] == 403 and response['code'] == 'not_authenticated':
                detail = _("Component could not authenticate against the AC - "
                           "authorizations could not be retrieved")
                raise PermissionDenied(detail=detail, code='not_authenticated_for_ac')
            logger.warn("Authorization component can't be accessed")
            return []

        return underscoreize(response['results'])

    def _get_auth(self):
        return Applicatie.objects.filter(client_ids__contains=[self.client_id])

    @transaction.atomic
    def _save_auth(self, auth_data):
        applicaties = []

        for applicatie_data in auth_data:
            applicatie_serializer = ApplicatieUuidSerializer(data=applicatie_data)
            uuid = get_uuid_from_path(applicatie_data['url'])
            applicatie_data['uuid'] = uuid
            applicatie_serializer.is_valid()
            applicaties.append(applicatie_serializer.save())

        return applicaties

    @cached_property
    def client_id(self) -> Union[str, None]:
        if self.encoded is None:
            return None

        # jwt check
        try:
            payload = jwt.decode(self.encoded, verify=False)
        except jwt.DecodeError:
            logger.info("Invalid JWT encountered")
            raise PermissionDenied(
                _('JWT could not be decoded. Possibly you made a copy-paste mistake.'),
                code='jwt-decode-error'
            )

        # get client_id
        try:
            client_id = payload['client_id']
        except KeyError:
            try:
                header = jwt.get_unverified_header(self.encoded)
            except jwt.DecodeError:
                logger.info("Invalid JWT encountered")
                raise PermissionDenied(
                    _('JWT could not be decoded. Possibly you made a copy-paste mistake.'),
                    code='jwt-decode-error'
                )
            else:
                try:
                    client_id = header['client_identifier']
                except KeyError:
                    raise PermissionDenied(
                        'Client identifier is niet aanwezig in JWT',
                        code='missing-client-identifier'
                    )
                else:
                    logger.warning(_('The support of authorization old format will be terminated soon. '
                                     'Please use a new format with the separate Authorization Component'))

        # find client_id in DB and retrieve it's secret
        try:
            jwt_secret = JWTSecret.objects.get(identifier=client_id)
        except JWTSecret.DoesNotExist:
            raise PermissionDenied(
                'Client identifier bestaat niet',
                code='invalid-client-identifier'
            )
        else:
            key = jwt_secret.secret

        # check signature of the token
        try:
            jwt.decode(self.encoded, key, algorithms='HS256')
        except jwt.InvalidSignatureError as exc:
            logger.exception("Invalid signature - possible payload tampering?")
            raise PermissionDenied(
                'Client credentials zijn niet geldig',
                code='invalid-jwt-signature'
            )

        return client_id

    def filter_vertrouwelijkheidaanduiding(self, base: QuerySet, value) -> QuerySet:
        if value is None:
            return base

        order_provided = VertrouwelijkheidsAanduiding.get_choice(value).order
        order_case = VertrouwelijkheidsAanduiding.get_order_expression("max_vertrouwelijkheidaanduiding")

        # In this case we are filtering Autorisatie model to look for auth which meets our needs.
        # Therefore we're only considering authorizations here that have a max_vertrouwelijkheidaanduiding
        # bigger or equal than what we're checking for the object.
        # In cases when we are filtering data objects (Zaak, InformatieObject etc) it's the other way around

        return base.annotate(max_vertr=order_case).filter(max_vertr__gte=order_provided)

    def filter_default(self, base: QuerySet, name, value) -> QuerySet:
        if value is None:
            return base

        return base.filter(**{name: value})

    def has_auth(self, scopes: List[str], **fields) -> bool:
        if scopes is None:
            return False

        scopes_provided = set()
        config = AuthorizationsConfig.get_solo()

        for applicatie in self.applicaties:
            # allow everything
            if applicatie.heeft_alle_autorisaties is True:
                return True

            autorisaties = applicatie.autorisaties.filter(component=config.component)

            # filter on all additional components
            for field_name, field_value in fields.items():
                if hasattr(self, f'filter_{field_name}'):
                    autorisaties = getattr(self, f'filter_{field_name}')(autorisaties, field_value)
                else:
                    autorisaties = self.filter_default(autorisaties, field_name, field_value)

            for autorisatie in autorisaties:
                scopes_provided.update(autorisatie.scopes)

        return scopes.is_contained_in(list(scopes_provided))


class AuthMiddleware:

    header = 'HTTP_AUTHORIZATION'
    auth_type = 'Bearer'

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.extract_jwt_payload(request)
        return self.get_response(request) if self.get_response else None

    def extract_jwt_payload(self, request):
        authorization = request.META.get(self.header, '')
        prefix = f"{self.auth_type} "
        if authorization.startswith(prefix):
            # grab the actual token
            encoded = authorization[len(prefix):]
        else:
            encoded = None

        request.jwt_payload = JWTPayload(encoded)
        request.jwt_auth = JWTAuth(encoded)


class APIVersionHeaderMiddleware:
    """
    Include a header specifying the API-version
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if self.get_response is None:
            return None

        response = self.get_response(request)

        # not an API response, exit early
        if not isinstance(response, Response):
            return response

        # set the header
        response[VERSION_HEADER] = settings.API_VERSION

        return response
