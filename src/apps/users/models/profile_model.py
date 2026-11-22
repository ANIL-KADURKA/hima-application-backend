import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class UserProfile(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(  # noqa: DJ001
        max_length=30,
        choices=Gender.choices,
        null=True,
        blank=True,
    )
    profile_photo_url = models.TextField(null=True, blank=True)  # noqa: DJ001
    bio = models.TextField(null=True, blank=True)  # noqa: DJ001
    country_code = models.CharField(max_length=5, null=True, blank=True)  # noqa: DJ001

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "user_profiles"

    def __str__(self) -> str:
        return f"Profile for {self.user.pk}"


class UserPreferences(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    language = models.ForeignKey(
        "users.AppLanguage",
        on_delete=models.SET_NULL,
        related_name="user_preferences",
        null=True,
        blank=True,
    )
    notification_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    dnd_enabled = models.BooleanField(default=False)
    dnd_until = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "user_preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.user.pk}"
