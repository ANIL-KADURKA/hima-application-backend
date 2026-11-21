from rest_framework import serializers

from apps.users.serializers.user_serializer import AuthenticatedUserSerializer


class SignInRequestSerializer(serializers.Serializer[dict[str, str]]):
    id_token = serializers.CharField(
        max_length=8192,
        trim_whitespace=True,
        help_text="Google or Firebase ID token obtained by the client.",
    )
    device_id = serializers.CharField(
        max_length=255,
        help_text="Stable identifier for the client device.",
    )
    device_name = serializers.CharField(
        max_length=150,
        required=False,
        help_text="Optional human-readable device name.",
    )
    platform = serializers.CharField(
        max_length=30,
        required=False,
        help_text="Optional client platform, such as ios or android.",
    )
    app_version = serializers.CharField(
        max_length=30,
        required=False,
        help_text="Optional client application version.",
    )


class RefreshRequestSerializer(serializers.Serializer[dict[str, str]]):
    refresh_token = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
        help_text="Refresh token returned by sign-in or the previous refresh.",
    )


class TokenResponseSerializer(serializers.Serializer[dict[str, object]]):
    token_type = serializers.CharField(help_text="Authorization scheme: Bearer.")
    access_token = serializers.CharField(
        help_text=(
            "Short-lived HIMA access token; send in the Authorization header "
            "as a Bearer token."
        )
    )
    refresh_token = serializers.CharField(
        help_text="Single-use refresh token. Store securely and rotate when refreshing."
    )
    expires_in = serializers.IntegerField(help_text="Access-token lifetime in seconds.")
    session_id = serializers.UUIDField(help_text="Identifier for the active session.")
    user = AuthenticatedUserSerializer()
