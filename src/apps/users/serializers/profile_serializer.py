from rest_framework import serializers

from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer[UserProfile]):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = UserProfile
        fields = [
            "display_name",
            "date_of_birth",
            "gender",
            "profile_photo_url",
            "bio",
            "country_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
