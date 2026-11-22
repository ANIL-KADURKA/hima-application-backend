import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class AuthProvider(models.TextChoices):
    GOOGLE = "google", "Google"
    FIREBASE_PHONE = "firebase_phone", "Firebase phone"


class UserAuthProvider(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_providers",
    )
    provider = models.CharField(max_length=30, choices=AuthProvider.choices)
    provider_user_id = models.CharField(max_length=255)
    provider_email = models.EmailField(max_length=255, null=True, blank=True)  # noqa: DJ001
    is_verified = models.BooleanField(default=False)

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "user_auth_providers"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="uq_auth_provider_subject",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_user_id}"
