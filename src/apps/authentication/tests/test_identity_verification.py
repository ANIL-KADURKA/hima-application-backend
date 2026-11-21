from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.authentication.services.errors import InvalidProviderToken
from apps.authentication.services.impl.firebase_identity_verifier_impl import (
    FirebaseIdentityTokenVerifierImpl,
)
from apps.authentication.services.impl.google_identity_verifier_impl import (
    GoogleIdentityTokenVerifierImpl,
)


@override_settings(GOOGLE_CLIENT_ID="hima-google-client")
def test_google_verifier_checks_audience_and_reads_verified_subject() -> None:
    claims = {
        "sub": "google-subject",
        "email": "User@Example.com",
        "email_verified": True,
        "name": "Hima User",
    }
    with patch(
        "apps.authentication.services.impl.google_identity_verifier_impl.id_token."
        "verify_oauth2_token",
        return_value=claims,
    ) as verify_token:
        identity = GoogleIdentityTokenVerifierImpl().verify("google-id-token")

    assert identity.provider == "google"
    assert identity.provider_user_id == "google-subject"
    assert identity.email == "User@Example.com"
    assert identity.email_verified is True
    verify_token.assert_called_once()
    assert verify_token.call_args.kwargs["audience"] == "hima-google-client"


def test_google_verifier_rejects_missing_email() -> None:
    with (
        override_settings(GOOGLE_CLIENT_ID="hima-google-client"),
        patch(
            "apps.authentication.services.impl.google_identity_verifier_impl.id_token."
            "verify_oauth2_token",
            return_value={"sub": "google-subject"},
        ),
        pytest.raises(InvalidProviderToken, match="no email"),
    ):
        GoogleIdentityTokenVerifierImpl().verify("google-id-token")


@override_settings(FIREBASE_PROJECT_ID="hima-firebase-project")
def test_firebase_verifier_requires_verified_phone_claim() -> None:
    with (
        patch(
            "apps.authentication.services.impl.firebase_identity_verifier_impl."
            "_firebase_app",
            return_value=object(),
        ),
        patch(
            "apps.authentication.services.impl.firebase_identity_verifier_impl.auth."
            "verify_id_token",
            return_value={"sub": "firebase-uid"},
        ),
        pytest.raises(InvalidProviderToken, match="verified phone"),
    ):
        FirebaseIdentityTokenVerifierImpl().verify("firebase-id-token")


@override_settings(FIREBASE_PROJECT_ID="hima-firebase-project")
def test_firebase_verifier_maps_uid_and_phone_claims() -> None:
    with (
        patch(
            "apps.authentication.services.impl.firebase_identity_verifier_impl."
            "_firebase_app",
            return_value=object(),
        ),
        patch(
            "apps.authentication.services.impl.firebase_identity_verifier_impl.auth."
            "verify_id_token",
            return_value={
                "uid": "firebase-uid",
                "phone_number": "+14155550123",
            },
        ),
    ):
        identity = FirebaseIdentityTokenVerifierImpl().verify("firebase-id-token")

    assert identity.provider == "firebase_phone"
    assert identity.provider_user_id == "firebase-uid"
    assert identity.phone_number == "+14155550123"
    assert identity.phone_verified is True
