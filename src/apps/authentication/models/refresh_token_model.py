import uuid

from django.db import models

from apps.core.models import TimestampedModel


class RefreshToken(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "authentication.UserSession",
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    token_jti = models.CharField(max_length=255, unique=True)
    token_hash = models.CharField(max_length=255, unique=True)
    token_family_id = models.UUIDField()
    parent_token = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="child_tokens",
        null=True,
        blank=True,
    )
    replaced_by_token = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replaced_tokens",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "refresh_tokens"
        indexes = [
            models.Index(fields=["token_family_id"], name="idx_refresh_tokens_family"),
            models.Index(fields=["expires_at"], name="idx_refresh_tokens_expires"),
        ]

    def __str__(self) -> str:
        return str(self.pk)
