from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.CharField()
    checked_at = serializers.DateTimeField()


class ErrorDetailSerializer(serializers.Serializer[dict[str, object]]):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(allow_null=True)


class ErrorResponseSerializer(serializers.Serializer[dict[str, object]]):
    error = ErrorDetailSerializer()
