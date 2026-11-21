from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.dao.impl import DjangoHealthCheckDAO
from apps.core.serializers import ErrorResponseSerializer, HealthResponseSerializer
from apps.core.services import HealthCheckService


class HealthCheckView(APIView):
    def get_authenticators(self) -> list[BaseAuthentication]:
        return []

    def get_permissions(self) -> list[BasePermission]:
        return []

    @extend_schema(
        summary="Check API and database health",
        description=(
            "Returns status and the UTC check timestamp when the database is "
            "reachable. This endpoint does not require authentication."
        ),
        responses={
            200: HealthResponseSerializer,
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["health"],
    )
    def get(self, request: Request) -> Response:
        del request
        result = HealthCheckService(DjangoHealthCheckDAO()).check()
        return Response(result)
