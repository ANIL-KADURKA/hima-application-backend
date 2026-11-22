from collections.abc import Mapping

from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    VerifiedIdentity,
)
from apps.authentication.services.errors import InvalidProviderToken


def normalize_claims(claims: object) -> Mapping[str, object]:
    if not isinstance(claims, dict):
        raise InvalidProviderToken("The identity provider returned invalid claims.")

    normalized: dict[str, object] = {}
    for key, value in claims.items():
        if isinstance(key, str):
            normalized[key] = value
    return normalized


def build_verified_identity(
    provider: AuthProviderName,
    claims: Mapping[str, object],
) -> VerifiedIdentity:
    subject = claims.get("sub")
    if provider == "firebase_phone":
        firebase_uid = claims.get("uid")
        if isinstance(firebase_uid, str) and firebase_uid:
            subject = firebase_uid
    if not isinstance(subject, str) or not subject:
        raise InvalidProviderToken("The identity token has no provider subject.")

    email = claims.get("email")
    phone_number = claims.get("phone_number")
    full_name = claims.get("name")
    return VerifiedIdentity(
        provider=provider,
        provider_user_id=subject,
        email=email if isinstance(email, str) and email else None,
        email_verified=claims.get("email_verified") is True,
        phone_number=(
            phone_number if isinstance(phone_number, str) and phone_number else None
        ),
        phone_verified=(
            provider == "firebase_phone"
            and isinstance(phone_number, str)
            and bool(phone_number)
        ),
        full_name=full_name if isinstance(full_name, str) and full_name else None,
    )
