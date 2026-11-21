import logging
from unittest.mock import patch
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from apps.authentication.dtos.authentication_dto import SessionCredentials
from apps.authentication.services.errors import InvalidProviderToken


class SuccessfulAuthenticationService:
    def sign_in(
        self,
        provider: str,
        token: str,
        metadata: object,
    ) -> SessionCredentials:
        del provider, token, metadata
        return SessionCredentials(
            user_id=str(uuid4()),
            email="hima@example.com",
            phone_number=None,
            full_name="Hima User",
            session_id=str(uuid4()),
            access_token="signed-access",
            refresh_token="opaque-refresh",
            expires_in=900,
        )


class RejectedAuthenticationService:
    def sign_in(
        self,
        provider: str,
        token: str,
        metadata: object,
    ) -> SessionCredentials:
        del provider, token, metadata
        raise InvalidProviderToken("The provider token is invalid.")


def test_google_endpoint_returns_hima_session_tokens() -> None:
    client = APIClient()
    with patch(
        "apps.authentication.views.authentication_view._authentication_service",
        return_value=SuccessfulAuthenticationService(),
    ):
        response = client.post(
            "/api/v1/auth/google/",
            {
                "id_token": "provider-id-token",
                "device_id": "device-1",
                "platform": "ios",
            },
            format="json",
        )

    assert response.status_code == 200
    assert response.data["token_type"] == "Bearer"
    assert response.data["refresh_token"] == "opaque-refresh"
    assert response.data["user"]["email"] == "hima@example.com"


def test_google_endpoint_rejects_invalid_provider_token() -> None:
    client = APIClient()
    with patch(
        "apps.authentication.views.authentication_view._authentication_service",
        return_value=RejectedAuthenticationService(),
    ):
        response = client.post(
            "/api/v1/auth/google/",
            {"id_token": "invalid", "device_id": "device-1"},
            format="json",
        )

    assert response.status_code == 401
    assert response.data == {
        "error": {
            "code": "invalid_provider_token",
            "message": "The provider token is invalid.",
            "details": None,
        }
    }


def test_validation_errors_use_the_shared_error_response() -> None:
    response = APIClient().post(
        "/api/v1/auth/google/",
        {"device_id": "device-1"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["message"] == "Request validation failed."
    assert "id_token" in response.data["error"]["details"]


def test_unexpected_api_errors_are_sanitized_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = APIClient(raise_request_exception=False)
    with (
        caplog.at_level(logging.ERROR, logger="apps.api"),
        patch(
            "apps.authentication.views.authentication_view._authentication_service",
            side_effect=RuntimeError("sensitive provider payload"),
        ),
    ):
        response = client.post(
            "/api/v1/auth/google/",
            {"id_token": "provider-id-token", "device_id": "device-1"},
            format="json",
        )

    assert response.status_code == 500
    assert response.data == {
        "error": {
            "code": "internal_server_error",
            "message": "An internal server error occurred.",
            "details": None,
        }
    }
    assert "sensitive provider payload" not in response.content.decode()
    assert "RuntimeError" in caplog.text
