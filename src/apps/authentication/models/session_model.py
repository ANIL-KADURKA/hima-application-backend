import uuid

from django.conf import settings
from django.core.validators import validate_ipv46_address
from django.db import models

from apps.core.models import TimestampedModel


class SessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class UserSession(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001
    platform = models.CharField(max_length=30, null=True, blank=True)  # noqa: DJ001
    app_version = models.CharField(max_length=30, null=True, blank=True)  # noqa: DJ001
    ip_address = models.CharField(  # noqa: DJ001
        max_length=45,
        null=True,
        blank=True,
        validators=[validate_ipv46_address],
    )
    user_agent = models.TextField(null=True, blank=True)  # noqa: DJ001
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "user_sessions"
        indexes = [
            models.Index(fields=["device_id"], name="idx_user_sessions_device"),
            models.Index(fields=["status"], name="idx_user_sessions_status"),
            models.Index(fields=["expires_at"], name="idx_user_sessions_expires"),
        ]

    def __str__(self) -> str:
        return f"{self.user.pk}:{self.device_id}"
