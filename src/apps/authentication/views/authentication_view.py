from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.authentication import SessionTokenAuthentication
from apps.authentication.daos.impl.django_authentication_dao import (
    DjangoAuthenticationDAO,
)
from apps.authentication.dtos.authentication_dto import (
    AuthProviderName,
    SessionCredentials,
    SessionMetadata,
)
from apps.authentication.models import UserSession
from apps.authentication.serializers.authentication_serializer import (
    RefreshRequestSerializer,
    SignInRequestSerializer,
    TokenResponseSerializer,
)
from apps.authentication.services.errors import (
    AccountUnavailable,
    IdentityLinkConflict,
    IdentityProviderUnavailable,
    InvalidProviderToken,
    ProviderNotConfigured,
    RefreshTokenRejected,
)
from apps.authentication.services.impl.authentication_service_impl import (
    AuthenticationServiceImpl,
)
from apps.authentication.services.impl.firebase_identity_verifier_impl import (
    FirebaseIdentityTokenVerifierImpl,
)
from apps.authentication.services.impl.google_identity_verifier_impl import (
    GoogleIdentityTokenVerifierImpl,
)
from apps.core.serializers import ErrorResponseSerializer
from apps.users.models import User
from apps.users.serializers.user_serializer import AuthenticatedUserSerializer

_TOKEN_RESPONSE_EXAMPLE = OpenApiExample(
    "HIMA session tokens",
    value={
        "token_type": "Bearer",  # nosec B105
        "access_token": "<hima-access-token>",  # nosec B105
        "refresh_token": "<one-time-refresh-token>",  # nosec B105
        "expires_in": 900,
        "session_id": "2f9f136c-558b-4c1c-9947-bc490dd8e813",
        "user": {
            "id": "09da468f-08cf-4e50-89b7-15e8169c42e2",
            "full_name": "Alex User",
            "email": "alex@example.com",
            "phone_number": None,
        },
    },
    response_only=True,
)

_SIGN_IN_REQUEST_EXAMPLE = OpenApiExample(
    "Sign-in request",
    value={
        "id_token": "<provider-id-token>",  # nosec B105
        "device_id": "device-123",
        "device_name": "Alex's phone",
        "platform": "ios",
        "app_version": "1.0.0",
    },
    request_only=True,
)


class IdentityProviderUnavailableAPIException(APIException):
    status_code = 503
    default_detail = "Identity provider verification is temporarily unavailable."
    default_code = "identity_provider_unavailable"


class IdentityLinkConflictAPIException(APIException):
    status_code = 409
    default_detail = "The verified identity conflicts with an existing account."
    default_code = "identity_link_conflict"


class InvalidProviderTokenAPIException(APIException):
    status_code = 401
    default_detail = "The provider ID token is invalid or expired."
    default_code = "invalid_provider_token"


class SessionTokenAuthenticationScheme(OpenApiAuthenticationExtension):  # type: ignore[no-untyped-call]
    target_class = "apps.authentication.authentication.SessionTokenAuthentication"
    name = "bearerAuth"

    def get_security_definition(self, auto_schema: object) -> dict[str, str]:
        del auto_schema
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "HIMA access token",
        }


def _authentication_service() -> AuthenticationServiceImpl:
    return AuthenticationServiceImpl(
        dao=DjangoAuthenticationDAO(),
        google_verifier=GoogleIdentityTokenVerifierImpl(),
        firebase_verifier=FirebaseIdentityTokenVerifierImpl(),
    )


def _session_metadata(
    request: Request,
    validated_data: dict[str, str],
) -> SessionMetadata:
    remote_addr = request.META.get("REMOTE_ADDR")
    user_agent = request.headers.get("User-Agent")
    return SessionMetadata(
        device_id=validated_data["device_id"],
        device_name=validated_data.get("device_name"),
        platform=validated_data.get("platform"),
        app_version=validated_data.get("app_version"),
        ip_address=remote_addr if isinstance(remote_addr, str) else None,
        user_agent=user_agent,
    )


def _token_response(credentials: SessionCredentials) -> Response:
    user_data = AuthenticatedUserSerializer(
        {
            "id": credentials.user_id,
            "full_name": credentials.full_name,
            "email": credentials.email,
            "phone_number": credentials.phone_number,
        }
    ).data
    body = {
        "token_type": "Bearer",  # nosec B105
        "access_token": credentials.access_token,
        "refresh_token": credentials.refresh_token,
        "expires_in": credentials.expires_in,
        "session_id": credentials.session_id,
        "user": user_data,
    }
    serializer = TokenResponseSerializer(data=body)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


class ProviderSignInView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    provider: AuthProviderName

    @extend_schema(
        summary="Sign in with an identity provider",
        description=(
            "Exchange a Google or Firebase ID token for a HIMA access token and "
            "refresh token. Firebase phone OTP is completed by the client; send "
            "the resulting Firebase ID token here, not the SMS code. The refresh "
            "token is single-use and must be replaced after each successful refresh."
        ),
        request=SignInRequestSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The provider ID token is invalid or expired.",
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The HIMA account is inactive or unavailable.",
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Verified identity details conflict with an account.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The provider is unavailable or not configured.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        examples=[_SIGN_IN_REQUEST_EXAMPLE, _TOKEN_RESPONSE_EXAMPLE],
        tags=["authentication"],
    )
    def post(self, request: Request) -> Response:
        serializer = SignInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            credentials = _authentication_service().sign_in(
                provider=self.provider,
                token=serializer.validated_data["id_token"],
                metadata=_session_metadata(request, serializer.validated_data),
            )
        except InvalidProviderToken as error:
            raise InvalidProviderTokenAPIException(str(error)) from error
        except AccountUnavailable as error:
            raise PermissionDenied(str(error)) from error
        except IdentityLinkConflict as error:
            raise IdentityLinkConflictAPIException(str(error)) from error
        except (IdentityProviderUnavailable, ProviderNotConfigured) as error:
            raise IdentityProviderUnavailableAPIException(str(error)) from error
        return _token_response(credentials)


@extend_schema_view(
    post=extend_schema(
        summary="Sign in with Google",
        description=(
            "Verify a Google ID token whose audience matches GOOGLE_CLIENT_ID, "
            "then create a HIMA session."
        ),
    )
)
class GoogleSignInView(ProviderSignInView):
    provider: AuthProviderName = "google"


@extend_schema_view(
    post=extend_schema(
        summary="Sign in with Firebase phone authentication",
        description=(
            "Verify the Firebase ID token issued after the client completes "
            "Firebase SMS/OTP sign-in, then create a HIMA session."
        ),
    )
)
class FirebasePhoneSignInView(ProviderSignInView):
    provider: AuthProviderName = "firebase_phone"


class RefreshTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Rotate a HIMA refresh token",
        description=(
            "Exchange a valid refresh token for a new access token and a new "
            "single-use refresh token. The submitted refresh token is invalidated."
        ),
        request=RefreshRequestSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The refresh token is invalid, expired, or revoked.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        examples=[
            OpenApiExample(
                "Refresh request",
                value={"refresh_token": "<one-time-refresh-token>"},  # nosec B105
                request_only=True,
            ),
            _TOKEN_RESPONSE_EXAMPLE,
        ],
        tags=["authentication"],
    )
    def post(self, request: Request) -> Response:
        serializer = RefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            credentials = _authentication_service().refresh(
                serializer.validated_data["refresh_token"]
            )
        except RefreshTokenRejected as error:
            raise AuthenticationFailed(str(error)) from error
        return _token_response(credentials)


class LogoutView(APIView):
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Revoke the current HIMA session",
        description="Revoke the session associated with the supplied bearer token.",
        request=None,
        responses={
            204: OpenApiResponse(description="Session revoked."),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The access token is missing, invalid, or expired.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected server error occurred.",
            ),
        },
        tags=["authentication"],
    )
    def post(self, request: Request) -> Response:
        session = request.auth
        if not isinstance(session, UserSession):
            raise AuthenticationFailed("A valid HIMA session is required.")
        user = request.user
        if not isinstance(user, User):
            raise AuthenticationFailed("Authentication is required.")
        _authentication_service().logout(str(session.pk), str(user.pk))
        return Response(status=204)
