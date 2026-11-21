from django.conf import settings
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from apps.authentication.dtos.authentication_dto import VerifiedIdentity
from apps.authentication.services.errors import (
    IdentityProviderUnavailable,
    InvalidProviderToken,
    ProviderNotConfigured,
)
from apps.authentication.services.impl.identity_claims import (
    build_verified_identity,
    normalize_claims,
)


class GoogleIdentityTokenVerifierImpl:
    def verify(self, token: str) -> VerifiedIdentity:
        if not settings.GOOGLE_CLIENT_ID:
            raise ProviderNotConfigured("GOOGLE_CLIENT_ID must be configured.")
        try:
            claims: object = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token,
                Request(),
                audience=settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as error:
            raise InvalidProviderToken("The Google ID token is invalid.") from error
        except google_auth_exceptions.GoogleAuthError as error:
            raise IdentityProviderUnavailable(
                "Google token verification is temporarily unavailable."
            ) from error

        identity = build_verified_identity("google", normalize_claims(claims))
        if identity.email is None:
            raise InvalidProviderToken("The Google ID token has no email address.")
        return identity
