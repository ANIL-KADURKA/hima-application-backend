from typing import Protocol

from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    SessionCredentials,
    SessionMetadata,
)


class AuthenticationServiceInterface(Protocol):
    def sign_in(
        self,
        provider: AuthProviderName,
        token: str,
        metadata: SessionMetadata,
    ) -> SessionCredentials:
        """Verify an identity and issue a HIMA session."""
        ...

    def refresh(self, refresh_token: str) -> SessionCredentials:
        """Rotate a refresh token and issue a new access token."""
        ...

    def logout(self, session_id: str, user_id: str) -> None:
        """Revoke a HIMA session."""
        ...
