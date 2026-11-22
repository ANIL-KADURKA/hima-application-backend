from dataclasses import dataclass
from typing import Literal

AuthProviderName = Literal["google", "firebase_phone"]


@dataclass(frozen=True)
class VerifiedIdentity:
    provider: AuthProviderName
    provider_user_id: str
    email: str | None = None
    email_verified: bool = False
    phone_number: str | None = None
    phone_verified: bool = False
    full_name: str | None = None


@dataclass(frozen=True)
class SessionMetadata:
    device_id: str
    device_name: str | None
    platform: str | None
    app_version: str | None
    ip_address: str | None
    user_agent: str | None


@dataclass(frozen=True)
class SessionCredentials:
    user_id: str
    email: str | None
    phone_number: str | None
    full_name: str | None
    session_id: str
    access_token: str
    refresh_token: str
    expires_in: int
