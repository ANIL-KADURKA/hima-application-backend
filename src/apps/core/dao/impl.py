"""Django ORM implementations of core persistence contracts."""

from datetime import UTC, datetime

from django.db import connection

from apps.core.dao.interfaces import HealthCheckDAO


class DjangoHealthCheckDAO(HealthCheckDAO):
    """Check database connectivity using the configured Django connection."""

    def check(self) -> datetime:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return datetime.now(UTC)
