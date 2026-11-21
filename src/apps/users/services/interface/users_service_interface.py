from typing import Protocol

from apps.users.models import User, UserPreferences, UserProfile


class UsersServiceInterface(Protocol):
    def get_profile(self, user: User) -> UserProfile:
        """Return the authenticated user's profile."""
        ...

    def get_preferences(self, user: User) -> UserPreferences:
        """Return the authenticated user's preferences."""
        ...
