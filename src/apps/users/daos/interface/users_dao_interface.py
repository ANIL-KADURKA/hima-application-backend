from typing import Protocol

from apps.users.models import User, UserPreferences, UserProfile


class UsersDAO(Protocol):
    def get_or_create_profile(self, user: User) -> UserProfile:
        """Return the user's profile, creating its default record if needed."""
        ...

    def get_or_create_preferences(self, user: User) -> UserPreferences:
        """Return the user's preferences, creating defaults if needed."""
        ...
