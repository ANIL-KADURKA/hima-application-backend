from typing import Protocol

from apps.authentication.dtos.authentication_dto import VerifiedIdentity


class IdentityTokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedIdentity:
        """Validate a provider token and return its verified identity claims."""
        ...
