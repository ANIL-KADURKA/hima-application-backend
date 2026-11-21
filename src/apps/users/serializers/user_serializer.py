from rest_framework import serializers

from apps.users.models import User


class UserSelfSerializer(serializers.ModelSerializer[User]):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = User
        fields = [
            "id",
            "full_name",
            "user_name",
            "email",
            "phone_number",
            "account_status",
            "is_email_verified",
            "is_phone_verified",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "phone_number",
            "account_status",
            "is_email_verified",
            "is_phone_verified",
            "created_at",
        ]


class AuthenticatedUserSerializer(serializers.Serializer[dict[str, str | None]]):
    id = serializers.CharField()
    full_name = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    phone_number = serializers.CharField(allow_null=True)
