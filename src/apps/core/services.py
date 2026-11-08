"""Core application services."""

from datetime import UTC

from apps.core.dao.interfaces import HealthCheckDAO


class HealthCheckService:
    def __init__(self, dao: HealthCheckDAO) -> None:
        self._dao = dao

    def check(self) -> dict[str, str]:
        checked_at = self._dao.check()
        return {"status": "ok", "checked_at": checked_at.astimezone(UTC).isoformat()}
