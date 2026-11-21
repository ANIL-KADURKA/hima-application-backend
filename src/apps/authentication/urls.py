from django.urls import path

from apps.authentication.views.authentication_view import (
    FirebasePhoneSignInView,
    GoogleSignInView,
    LogoutView,
    RefreshTokenView,
)

urlpatterns = [
    path("google/", GoogleSignInView.as_view(), name="google-sign-in"),
    path("firebase/", FirebasePhoneSignInView.as_view(), name="firebase-phone-sign-in"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh-token"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
