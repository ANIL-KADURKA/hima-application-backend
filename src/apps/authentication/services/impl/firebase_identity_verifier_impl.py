import firebase_admin  # type: ignore[import-untyped]
from django.conf import settings
from firebase_admin import auth, exceptions

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

_FIREBASE_APP_NAME = "hima"


def _firebase_app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app(_FIREBASE_APP_NAME)
    except ValueError:
        if not settings.FIREBASE_PROJECT_ID:
            raise ProviderNotConfigured(
                "FIREBASE_PROJECT_ID must be configured."
            ) from None
        return firebase_admin.initialize_app(
            options={"projectId": settings.FIREBASE_PROJECT_ID},
            name=_FIREBASE_APP_NAME,
        )


class FirebaseIdentityTokenVerifierImpl:
    def verify(self, token: str) -> VerifiedIdentity:
        app = _firebase_app()
        try:
            claims = auth.verify_id_token(token, app=app)
        except (ValueError, auth.InvalidIdTokenError) as error:
            raise InvalidProviderToken("The Firebase ID token is invalid.") from error
        except exceptions.FirebaseError as error:
            raise IdentityProviderUnavailable(
                "Firebase token verification is temporarily unavailable."
            ) from error

        identity = build_verified_identity("firebase_phone", normalize_claims(claims))
        if identity.phone_number is None:
            raise InvalidProviderToken(
                "The Firebase ID token has no verified phone number."
            )
        return identity
