from django.conf import settings

from apps.authentication.daos.interface.authentication_dao_interface import (
    AuthenticationDAO,
)
from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    SessionCredentials,
    SessionMetadata,
    VerifiedIdentity,
)
from apps.authentication.services.errors import RefreshTokenRejected
from apps.authentication.services.interface.authentication_service_interface import (
    AuthenticationServiceInterface,
)
from apps.authentication.services.interface.identity_verifier_interface import (
    IdentityTokenVerifier,
)
from apps.authentication.utils.access_tokens import encode_access_token
from apps.users.models import User


class AuthenticationServiceImpl(AuthenticationServiceInterface):
    def __init__(
        self,
        dao: AuthenticationDAO,
        google_verifier: IdentityTokenVerifier,
        firebase_verifier: IdentityTokenVerifier,
    ) -> None:
        self._dao = dao
        self._verifiers: dict[AuthProviderName, IdentityTokenVerifier] = {
            "google": google_verifier,
            "firebase_phone": firebase_verifier,
        }

    def sign_in(
        self,
        provider: AuthProviderName,
        token: str,
        metadata: SessionMetadata,
    ) -> SessionCredentials:
        verifier = self._verifiers[provider]
        identity: VerifiedIdentity = verifier.verify(token)
        user = self._dao.resolve_identity(identity)
        session, refresh_token = self._dao.create_session(
            user=user,
            provider=identity.provider,
            metadata=metadata,
        )
        return self._credentials(user, str(session.pk), refresh_token)

    def refresh(self, refresh_token: str) -> SessionCredentials:
        rotated = self._dao.rotate_refresh_token(refresh_token)
        if rotated is None:
            raise RefreshTokenRejected("The refresh token is no longer valid.")

        session, replacement_token = rotated
        return self._credentials(session.user, str(session.pk), replacement_token)

    def logout(self, session_id: str, user_id: str) -> None:
        session = self._dao.get_active_session(session_id, user_id)
        if session is not None:
            self._dao.revoke_session(session, "user_logout")

    @staticmethod
    def _credentials(
        user: User,
        session_id: str,
        refresh_token: str,
    ) -> SessionCredentials:
        return SessionCredentials(
            user_id=str(user.pk),
            email=user.email,
            phone_number=user.phone_number,
            full_name=user.full_name,
            session_id=session_id,
            access_token=encode_access_token(session_id, str(user.pk)),
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
        )
