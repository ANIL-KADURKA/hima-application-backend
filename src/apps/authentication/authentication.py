from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.authentication.daos.impl.django_authentication_dao import (
    DjangoAuthenticationDAO,
)
from apps.authentication.utils.access_tokens import decode_access_token
from apps.users.models import User


class SessionTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[User, object] | None:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer":
            return None
        if not token or " " in token:
            raise AuthenticationFailed("Invalid bearer token.")

        claims = decode_access_token(token)
        if claims is None:
            raise AuthenticationFailed("Invalid or expired access token.")

        session_id, user_id = claims
        session = DjangoAuthenticationDAO().get_active_session(session_id, user_id)
        if session is None or not session.user.is_active:
            raise AuthenticationFailed("The session is no longer active.")
        return session.user, session

    def authenticate_header(self, request: Request) -> str:
        del request
        return "Bearer"
