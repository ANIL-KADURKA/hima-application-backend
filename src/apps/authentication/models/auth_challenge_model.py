import uuid

from django.conf import settings
from django.db import models


class AuthChannel(models.TextChoices):
    EMAIL = "email", "Email"


class AuthChallengePurpose(models.TextChoices):
    EMAIL_LOGIN = "email_login", "Email login"
    EMAIL_VERIFICATION = "email_verification", "Email verification"


class AuthChallengeStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Verified"
    EXPIRED = "expired", "Expired"
    LOCKED = "locked", "Locked"
    CANCELLED = "cancelled", "Cancelled"


class AuthChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="auth_challenges",
        null=True,
        blank=True,
    )
    channel = models.CharField(
        max_length=20,
        choices=AuthChannel.choices,
        default=AuthChannel.EMAIL,
    )
    purpose = models.CharField(max_length=30, choices=AuthChallengePurpose.choices)
    destination = models.CharField(max_length=255)
    code_hash = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=AuthChallengeStatus.choices,
        default=AuthChallengeStatus.PENDING,
    )
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_challenges"
        indexes = [
            models.Index(fields=["destination"], name="idx_auth_challenges_dest"),
            models.Index(fields=["status"], name="idx_auth_challenges_status"),
            models.Index(fields=["expires_at"], name="idx_auth_challenges_expires"),
        ]

    def __str__(self) -> str:
        return f"{self.purpose}:{self.destination}"
