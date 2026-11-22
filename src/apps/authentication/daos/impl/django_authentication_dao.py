import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    SessionMetadata,
    VerifiedIdentity,
)
from apps.authentication.models import (
    AuthSecurityEvent,
    LoginHistory,
    LoginMethod,
    LoginStatus,
    RefreshToken,
    SessionStatus,
    UserAuthProvider,
    UserSession,
)
from apps.authentication.services.errors import AccountUnavailable, IdentityLinkConflict
from apps.users.models import AccountStatus, User, UserPreferences, UserProfile


class DjangoAuthenticationDAO:
    def resolve_identity(self, identity: VerifiedIdentity) -> User:
        with transaction.atomic():
            provider_link = (
                UserAuthProvider.objects.select_for_update()
                .select_related("user")
                .filter(
                    provider=identity.provider,
                    provider_user_id=identity.provider_user_id,
                )
                .first()
            )
            if provider_link is not None:
                user = provider_link.user
                self._require_active_user(user)
                self._update_verified_contacts(user, identity)
                self._ensure_user_defaults(user, identity)
                return user

            email_user = self._find_email_user(identity)
            phone_user = self._find_phone_user(identity)
            if (
                email_user is not None
                and phone_user is not None
                and email_user.pk != phone_user.pk
            ):
                raise IdentityLinkConflict(
                    "The verified email and phone belong to different accounts."
                )

            matched_user = email_user or phone_user
            if matched_user is None:
                resolved_user = User.create_user(
                    email=self._normalized_email(identity),
                    phone_number=(
                        identity.phone_number if identity.phone_verified else None
                    ),
                    full_name=identity.full_name,
                )
            else:
                resolved_user = matched_user

            self._require_active_user(resolved_user)
            self._update_verified_contacts(resolved_user, identity)
            UserAuthProvider.objects.create(
                user=resolved_user,
                provider=identity.provider,
                provider_user_id=identity.provider_user_id,
                provider_email=self._normalized_email(identity),
                is_verified=True,
            )
            self._ensure_user_defaults(resolved_user, identity)
            return resolved_user

    def create_session(
        self,
        user: User,
        provider: AuthProviderName,
        metadata: SessionMetadata,
    ) -> tuple[UserSession, str]:
        now = timezone.now()
        refresh_expires_at = now + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS)
        with transaction.atomic():
            session = UserSession.objects.create(
                user=user,
                device_id=metadata.device_id,
                device_name=metadata.device_name,
                platform=metadata.platform,
                app_version=metadata.app_version,
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
                last_used_at=now,
                expires_at=refresh_expires_at,
            )
            raw_token = self._new_refresh_token(
                session=session,
                family_id=uuid.uuid4(),
                expires_at=refresh_expires_at,
            )[1]
            user.last_login_at = now
            user.save(update_fields=["last_login_at", "updated_at"])
            LoginHistory.objects.create(
                user=user,
                session=session,
                login_method=self._login_method(provider),
                login_status=LoginStatus.SUCCESS,
                ip_address=metadata.ip_address,
                device_id=metadata.device_id,
                user_agent=metadata.user_agent,
            )
        return session, raw_token

    def rotate_refresh_token(self, raw_token: str) -> tuple[UserSession, str] | None:
        now = timezone.now()
        token_hash = self._hash_refresh_token(raw_token)
        with transaction.atomic():
            refresh_token = (
                RefreshToken.objects.select_for_update()
                .select_related("session__user")
                .filter(token_hash=token_hash)
                .first()
            )
            if refresh_token is None:
                return None

            session = refresh_token.session
            if (
                refresh_token.used_at is not None
                or refresh_token.revoked_at is not None
            ):
                RefreshToken.objects.filter(
                    token_family_id=refresh_token.token_family_id,
                    revoked_at__isnull=True,
                ).update(revoked_at=now)
                self._revoke_session_record(session, "refresh_token_reuse", now)
                AuthSecurityEvent.objects.create(
                    user=session.user,
                    session=session,
                    event_type="refresh_token_reuse",
                    severity="high",
                    description="A previously used refresh token was presented.",
                )
                return None

            if (
                refresh_token.expires_at <= now
                or session.status != SessionStatus.ACTIVE
                or session.expires_at is None
                or session.expires_at <= now
                or not session.user.is_active
            ):
                return None

            replacement = self._new_refresh_token(
                session=session,
                family_id=refresh_token.token_family_id,
                expires_at=refresh_token.expires_at,
                parent_token=refresh_token,
            )
            refresh_token.used_at = now
            refresh_token.replaced_by_token = replacement[0]
            refresh_token.save(update_fields=["used_at", "replaced_by_token"])
            session.last_used_at = now
            session.save(update_fields=["last_used_at", "updated_at"])
            return session, replacement[1]

    def get_active_session(self, session_id: str, user_id: str) -> UserSession | None:
        now = timezone.now()
        session = (
            UserSession.objects.select_related("user")
            .filter(
                id=session_id,
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                expires_at__gt=now,
                user__account_status=AccountStatus.ACTIVE,
            )
            .first()
        )
        if session is not None:
            session.last_used_at = now
            session.save(update_fields=["last_used_at", "updated_at"])
        return session

    def revoke_session(self, session: UserSession, reason: str) -> None:
        now = timezone.now()
        with transaction.atomic():
            locked_session = UserSession.objects.select_for_update().get(pk=session.pk)
            self._revoke_session_record(locked_session, reason, now)
            RefreshToken.objects.filter(
                session=locked_session,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

    @staticmethod
    def _find_email_user(identity: VerifiedIdentity) -> User | None:
        email = DjangoAuthenticationDAO._normalized_email(identity)
        if email is None:
            return None
        existing_user = User.objects.select_for_update().filter(email=email).first()
        if existing_user is not None and not identity.email_verified:
            raise IdentityLinkConflict(
                "An unverified email cannot be used to link an existing account."
            )
        return existing_user

    @staticmethod
    def _find_phone_user(identity: VerifiedIdentity) -> User | None:
        if not identity.phone_verified or identity.phone_number is None:
            return None
        return (
            User.objects.select_for_update()
            .filter(phone_number=identity.phone_number)
            .first()
        )

    @staticmethod
    def _normalized_email(identity: VerifiedIdentity) -> str | None:
        if identity.email is None:
            return None
        return identity.email.strip().casefold()

    @staticmethod
    def _update_verified_contacts(user: User, identity: VerifiedIdentity) -> None:
        updated_fields: list[str] = []
        email = DjangoAuthenticationDAO._normalized_email(identity)
        if identity.email_verified and email is not None:
            if user.email not in (None, email):
                raise IdentityLinkConflict(
                    "The verified email conflicts with the linked HIMA account."
                )
            if user.email != email or not user.is_email_verified:
                user.email = email
                user.is_email_verified = True
                updated_fields.extend(["email", "is_email_verified"])

        if identity.phone_verified and identity.phone_number is not None:
            if user.phone_number not in (None, identity.phone_number):
                raise IdentityLinkConflict(
                    "The verified phone conflicts with the linked HIMA account."
                )
            if user.phone_number != identity.phone_number or not user.is_phone_verified:
                user.phone_number = identity.phone_number
                user.is_phone_verified = True
                updated_fields.extend(["phone_number", "is_phone_verified"])

        if updated_fields:
            user.save(update_fields=[*updated_fields, "updated_at"])

    @staticmethod
    def _ensure_user_defaults(user: User, identity: VerifiedIdentity) -> None:
        UserProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": identity.full_name},
        )
        UserPreferences.objects.get_or_create(user=user)

    @staticmethod
    def _require_active_user(user: User) -> None:
        if not user.is_active:
            raise AccountUnavailable("This HIMA account is not active.")

    def _new_refresh_token(
        self,
        session: UserSession,
        family_id: uuid.UUID,
        expires_at: datetime,
        parent_token: RefreshToken | None = None,
    ) -> tuple[RefreshToken, str]:
        raw_token = secrets.token_urlsafe(48)
        token = RefreshToken.objects.create(
            session=session,
            token_jti=uuid.uuid4().hex,
            token_hash=self._hash_refresh_token(raw_token),
            token_family_id=family_id,
            parent_token=parent_token,
            expires_at=expires_at,
        )
        return token, raw_token

    @staticmethod
    def _hash_refresh_token(raw_token: str) -> str:
        return hmac.new(
            settings.SECRET_KEY.encode(),
            raw_token.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _revoke_session_record(
        session: UserSession,
        reason: str,
        now: datetime,
    ) -> None:
        session.status = SessionStatus.REVOKED
        session.revoked_at = now
        session.revoke_reason = reason
        session.save(
            update_fields=["status", "revoked_at", "revoke_reason", "updated_at"]
        )

    @staticmethod
    def _login_method(provider: AuthProviderName) -> str:
        if provider == "google":
            return LoginMethod.GOOGLE
        return LoginMethod.FIREBASE_PHONE
