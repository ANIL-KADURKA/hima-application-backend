from django.conf import settings
from django.core import signing

_ACCESS_TOKEN_SALT = "hima.access-token"  # nosec B105


def encode_access_token(session_id: str, user_id: str) -> str:
    """Create a signed, short-lived HIMA access token."""
    return signing.dumps(
        {"sid": session_id, "uid": user_id},
        salt=_ACCESS_TOKEN_SALT,
        compress=True,
    )


def decode_access_token(token: str) -> tuple[str, str] | None:
    """Validate an access token and return its session and user identifiers."""
    try:
        claims = signing.loads(
            token,
            salt=_ACCESS_TOKEN_SALT,
            max_age=settings.ACCESS_TOKEN_TTL_SECONDS,
        )
    except (signing.BadSignature, signing.SignatureExpired, TypeError):
        return None

    if not isinstance(claims, dict):
        return None
    session_id = claims.get("sid")
    user_id = claims.get("uid")
    if not isinstance(session_id, str) or not isinstance(user_id, str):
        return None
    return session_id, user_id
