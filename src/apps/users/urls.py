from django.urls import path

from apps.users.views.users_view import (
    UserPreferencesView,
    UserProfileView,
    UserSelfView,
)

urlpatterns = [
    path("me/", UserSelfView.as_view(), name="user-self"),
    path("me/profile/", UserProfileView.as_view(), name="user-profile"),
    path("me/preferences/", UserPreferencesView.as_view(), name="user-preferences"),
]
