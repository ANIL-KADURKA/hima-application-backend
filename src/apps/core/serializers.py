from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.CharField()
    checked_at = serializers.DateTimeField()
