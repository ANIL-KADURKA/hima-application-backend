import uuid

from django.db import models

from apps.core.models import TimestampedModel


class RateLimitCounter(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    limit_key = models.CharField(max_length=64)
    scope = models.CharField(max_length=50)
    window_start = models.DateTimeField()
    window_seconds = models.IntegerField()
    hit_count = models.IntegerField(default=1)
    blocked_until = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "rate_limit_counters"
        constraints = [
            models.UniqueConstraint(
                fields=["limit_key", "scope", "window_start"],
                name="uq_rate_limit_key_scope_window",
            )
        ]
        indexes = [
            models.Index(fields=["blocked_until"], name="idx_rate_limit_blocked_until")
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.window_start.isoformat()}"
