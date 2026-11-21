from __future__ import annotations

import uuid
from typing import ClassVar

from django.core.validators import MinLengthValidator
from django.db import models

from apps.core.models import TimestampedModel


class AccountStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"
    DELETED = "deleted", "Deleted"


class User(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001
    user_name = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[MinLengthValidator(4)],
    )  # noqa: DJ001
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)  # noqa: DJ001
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # noqa: DJ001
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)  # noqa: DJ001
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD: ClassVar[str] = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "users"

    @classmethod
    def create_user(
        cls,
        email: str | None = None,
        phone_number: str | None = None,
        full_name: str | None = None,
    ) -> User:
        if email is None and phone_number is None:
            raise ValueError("A user must have an email address or phone number.")

        normalized_email = email.strip().casefold() if email else None
        user = cls(
            email=normalized_email,
            phone_number=phone_number,
            full_name=full_name,
        )
        user.save()
        return user

    @property
    def is_active(self) -> bool:
        return self.account_status == AccountStatus.ACTIVE

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_username(self) -> str:
        return self.email or self.phone_number or str(self.pk)

    def __str__(self) -> str:
        return self.email or self.phone_number or str(self.pk)
