from typing import Protocol

from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    SessionMetadata,
    VerifiedIdentity,
)
from apps.authentication.models import UserSession
from apps.users.models import User


class AuthenticationDAO(Protocol):
    def resolve_identity(self, identity: VerifiedIdentity) -> User:
        """Find or create the HIMA user associated with a verified identity."""
        ...

    def create_session(
        self,
        user: User,
        provider: AuthProviderName,
        metadata: SessionMetadata,
    ) -> tuple[UserSession, str]:
        """Create an authenticated session and its first refresh token."""
        ...

    def rotate_refresh_token(self, raw_token: str) -> tuple[UserSession, str] | None:
        """Rotate an active refresh token, returning None when it is rejected."""
        ...

    def get_active_session(self, session_id: str, user_id: str) -> UserSession | None:
        """Return a live session belonging to the claimed user."""
        ...

    def revoke_session(self, session: UserSession, reason: str) -> None:
        """Revoke a session and all refresh tokens associated with it."""
        ...
