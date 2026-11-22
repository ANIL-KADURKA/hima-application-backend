from rest_framework import serializers

from apps.users.models import UserPreferences


class UserPreferencesSerializer(serializers.ModelSerializer[UserPreferences]):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = UserPreferences
        fields = [
            "language",
            "notification_enabled",
            "sound_enabled",
            "dnd_enabled",
            "dnd_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
