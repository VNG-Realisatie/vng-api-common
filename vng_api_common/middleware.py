# https://pyjwt.readthedocs.io/en/latest/usage.html#reading-headers-without-validation
# -> we can put the organization/service in the headers itself
import logging
from typing import List, Union

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

import jwt
from djangorestframework_camel_case.util import underscoreize
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response


from vng_api_common.authorizations.models import AuthorizationsConfig
from vng_api_common.authorizations.models import Applicatie
from vng_api_common.authorizations.serializers import ApplicatieUuidSerializer

from .constants import VERSION_HEADER
from .models import JWTSecret
from .scopes import Scope
from .utils import get_identifier_from_path

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

    def _request_auth(self) -> list:
        client = AuthorizationsConfig.get_client()

        response = client.list(
            'applicatie',
            query_params={'client_ids': self.client_id}
        )
        return underscoreize(response['results'])

    def _get_auth(self):
        return Applicatie.objects.filter(client_ids__contains=[self.client_id])

    @transaction.atomic
    def _save_auth(self, auth_data):
        applicaties = []

        for applicatie_data in auth_data:
            uuid = get_identifier_from_path(applicatie_data['url'])
            applicatie_data['uuid'] = uuid
            applicatie_serializer = ApplicatieUuidSerializer(data=applicatie_data)
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

    def has_auth(self, scopes: List[str], zaaktype: Union[str, None],
                 vertrouwelijkheidaanduiding: Union[str, None]) -> bool:

        if scopes is None:
            return False

        scopes_provided = set()
        config = AuthorizationsConfig.get_solo()

        for applicatie in self.applicaties:
            # allow everything
            if applicatie.heeft_alle_autorisaties is True:
                return True

            # consider all scopes at all zaaktypes and vertrouwelijkheidaanduiding
            zaaktype_q = Q(zaaktype=zaaktype) if zaaktype is not None else Q()

            for autorisatie in applicatie.autorisaties.filter(zaaktype_q, component=config.component):
                vertrouwelijkheidaanduiding_ok = (
                    vertrouwelijkheidaanduiding is None
                    or autorisatie.satisfy_vertrouwelijkheid(vertrouwelijkheidaanduiding)  # noqa
                )

                if vertrouwelijkheidaanduiding_ok:
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
