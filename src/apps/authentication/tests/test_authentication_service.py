import uuid

import pytest
from django.test import override_settings

from apps.authentication.dtos.authentication_dto import (
    SessionMetadata,
    VerifiedIdentity,
)
from apps.authentication.models import UserSession
from apps.authentication.services.errors import RefreshTokenRejected
from apps.authentication.services.impl.authentication_service_impl import (
    AuthenticationServiceImpl,
)
from apps.authentication.utils.access_tokens import decode_access_token
from apps.users.models import User


class FakeVerifier:
    def __init__(self, identity: VerifiedIdentity) -> None:
        self._identity = identity

    def verify(self, token: str) -> VerifiedIdentity:
        assert token == "provider-token"
        return self._identity


class FakeDAO:
    def __init__(self, user: User, session_id: uuid.UUID) -> None:
        self._user = user
        self._session_id = session_id
        self.identity: VerifiedIdentity | None = None
        self.metadata: SessionMetadata | None = None

    def resolve_identity(self, identity: VerifiedIdentity) -> User:
        self.identity = identity
        return self._user

    def create_session(
        self,
        user: User,
        provider: str,
        metadata: SessionMetadata,
    ) -> tuple[UserSession, str]:
        del provider
        self.metadata = metadata
        return UserSession(id=self._session_id, user=user), "opaque-refresh-token"

    def rotate_refresh_token(self, raw_token: str) -> tuple[UserSession, str] | None:
        del raw_token
        return None

    def get_active_session(self, session_id: str, user_id: str) -> UserSession | None:
        del session_id, user_id
        return None

    def revoke_session(self, session: UserSession, reason: str) -> None:
        del session, reason


@override_settings(ACCESS_TOKEN_TTL_SECONDS=300)
def test_sign_in_issues_hima_tokens_after_provider_verification() -> None:
    identity = VerifiedIdentity(
        provider="google",
        provider_user_id="google-subject",
        email="hima@example.com",
        email_verified=True,
    )
    user = User(id=uuid.uuid4(), email="hima@example.com", full_name="Hima User")
    session_id = uuid.uuid4()
    dao = FakeDAO(user, session_id)
    service = AuthenticationServiceImpl(
        dao=dao,
        google_verifier=FakeVerifier(identity),
        firebase_verifier=FakeVerifier(
            VerifiedIdentity(provider="firebase_phone", provider_user_id="firebase-uid")
        ),
    )
    metadata = SessionMetadata(
        device_id="device-1",
        device_name=None,
        platform="ios",
        app_version="1.0",
        ip_address=None,
        user_agent=None,
    )

    credentials = service.sign_in("google", "provider-token", metadata)

    assert credentials.user_id == str(user.pk)
    assert credentials.session_id == str(session_id)
    assert credentials.refresh_token == "opaque-refresh-token"
    assert credentials.phone_number is None
    assert credentials.expires_in == 300
    assert dao.identity == identity
    assert dao.metadata == metadata
    assert decode_access_token(credentials.access_token) == (
        str(session_id),
        str(user.pk),
    )


def test_refresh_rejects_unrecognized_token() -> None:
    user = User(id=uuid.uuid4(), email="hima@example.com")
    dao = FakeDAO(user, uuid.uuid4())
    service = AuthenticationServiceImpl(
        dao=dao,
        google_verifier=FakeVerifier(
            VerifiedIdentity(provider="google", provider_user_id="google-subject")
        ),
        firebase_verifier=FakeVerifier(
            VerifiedIdentity(provider="firebase_phone", provider_user_id="firebase-uid")
        ),
    )

    with pytest.raises(RefreshTokenRejected):
        service.refresh("invalid-refresh-token")
