"""Persistence contracts used by the core application."""

from datetime import datetime
from typing import Protocol


class HealthCheckDAO(Protocol):
    """Contract for checking persistence availability."""

    def check(self) -> datetime:
        """Return the database server time when persistence is available."""
        ...
