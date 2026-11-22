class InvalidProviderToken(Exception):
    """Raised when an external identity token is invalid or expired."""


class IdentityProviderUnavailable(Exception):
    """Raised when an identity provider cannot be reached."""


class ProviderNotConfigured(Exception):
    """Raised when a required identity provider setting is missing."""


class AccountUnavailable(Exception):
    """Raised when an identity belongs to a disabled HIMA account."""


class IdentityLinkConflict(Exception):
    """Raised when verified identity details conflict with existing accounts."""


class RefreshTokenRejected(Exception):
    """Raised when a refresh token is invalid, expired, or revoked."""
