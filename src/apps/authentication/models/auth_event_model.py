import uuid

from django.conf import settings
from django.core.validators import validate_ipv46_address
from django.db import models


class LoginMethod(models.TextChoices):
    GOOGLE = "GOOGLE", "Google"
    FIREBASE_PHONE = "FIREBASE_PHONE", "Firebase phone"
    EMAIL_OTP = "EMAIL_OTP", "Email OTP"


class LoginStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    BLOCKED = "BLOCKED", "Blocked"


class LoginHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="login_history",
        null=True,
        blank=True,
    )
    session = models.ForeignKey(
        "authentication.UserSession",
        on_delete=models.SET_NULL,
        related_name="login_history",
        null=True,
        blank=True,
    )
    login_method = models.CharField(max_length=30, choices=LoginMethod.choices)
    login_status = models.CharField(max_length=30, choices=LoginStatus.choices)
    ip_address = models.CharField(  # noqa: DJ001
        max_length=45,
        null=True,
        blank=True,
        validators=[validate_ipv46_address],
    )
    device_id = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    user_agent = models.TextField(null=True, blank=True)  # noqa: DJ001
    failure_reason = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "login_history"
        indexes = [
            models.Index(fields=["ip_address"], name="idx_login_history_ip"),
            models.Index(fields=["created_at"], name="idx_login_history_created"),
            models.Index(fields=["login_status"], name="idx_login_history_status"),
        ]

    def __str__(self) -> str:
        return f"{self.login_method}:{self.login_status}"


class AuthSecurityEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="security_events",
        null=True,
        blank=True,
    )
    session = models.ForeignKey(
        "authentication.UserSession",
        on_delete=models.SET_NULL,
        related_name="security_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=60)
    severity = models.CharField(max_length=20, default="info")
    ip_address = models.CharField(  # noqa: DJ001
        max_length=45,
        null=True,
        blank=True,
        validators=[validate_ipv46_address],
    )
    device_id = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001
    user_agent = models.TextField(null=True, blank=True)  # noqa: DJ001
    description = models.TextField(null=True, blank=True)  # noqa: DJ001
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_security_events"
        indexes = [
            models.Index(fields=["event_type"], name="idx_auth_events_type"),
            models.Index(fields=["severity"], name="idx_auth_events_severity"),
            models.Index(fields=["created_at"], name="idx_auth_events_created"),
        ]

    def __str__(self) -> str:
        return self.event_type
