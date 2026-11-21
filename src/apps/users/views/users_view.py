from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.authentication import SessionTokenAuthentication
from apps.core.serializers import ErrorResponseSerializer
from apps.users.daos.impl.django_users_dao import DjangoUsersDAO
from apps.users.models import User
from apps.users.serializers.preferences_serializer import UserPreferencesSerializer
from apps.users.serializers.profile_serializer import UserProfileSerializer
from apps.users.serializers.user_serializer import UserSelfSerializer
from apps.users.services.impl.users_service_impl import UsersServiceImpl


def _authenticated_user(request: Request) -> User:
    if not isinstance(request.user, User):
        raise AuthenticationFailed("Authentication is required.")
    return request.user


class UserSelfView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get the authenticated user",
        description=(
            "Return the account associated with the supplied HIMA bearer token."
        ),
        responses={
            200: UserSelfSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def get(self, request: Request) -> Response:
        user = _authenticated_user(request)
        return Response(UserSelfSerializer(user).data)

    @extend_schema(
        summary="Update the authenticated user's name or username",
        description=(
            "Partially update the editable account fields. Email, phone number, "
            "verification state, and account status are read-only."
        ),
        request=UserSelfSerializer,
        responses={
            200: UserSelfSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def patch(self, request: Request) -> Response:
        user = _authenticated_user(request)
        serializer = UserSelfSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(UserSelfSerializer(serializer.save()).data)


class UserProfileView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get the authenticated user's profile",
        description="Return the profile associated with the authenticated account.",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def get(self, request: Request) -> Response:
        profile = UsersServiceImpl(DjangoUsersDAO()).get_profile(
            _authenticated_user(request)
        )
        return Response(UserProfileSerializer(profile).data)

    @extend_schema(
        summary="Update the authenticated user's profile",
        description="Partially update profile details for the authenticated account.",
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def patch(self, request: Request) -> Response:
        profile = UsersServiceImpl(DjangoUsersDAO()).get_profile(
            _authenticated_user(request)
        )
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(UserProfileSerializer(serializer.save()).data)


class UserPreferencesView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get the authenticated user's preferences",
        description="Return application preferences for the authenticated account.",
        responses={
            200: UserPreferencesSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def get(self, request: Request) -> Response:
        preferences = UsersServiceImpl(DjangoUsersDAO()).get_preferences(
            _authenticated_user(request)
        )
        return Response(UserPreferencesSerializer(preferences).data)

    @extend_schema(
        summary="Update the authenticated user's preferences",
        description=(
            "Partially update application preferences for the authenticated account."
        ),
        request=UserPreferencesSerializer,
        responses={
            200: UserPreferencesSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["users"],
    )
    def patch(self, request: Request) -> Response:
        preferences = UsersServiceImpl(DjangoUsersDAO()).get_preferences(
            _authenticated_user(request)
        )
        serializer = UserPreferencesSerializer(
            preferences,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        return Response(UserPreferencesSerializer(serializer.save()).data)
