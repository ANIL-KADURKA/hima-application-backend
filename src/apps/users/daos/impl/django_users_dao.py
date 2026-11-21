from apps.users.daos.interface.users_dao_interface import UsersDAO
from apps.users.models import User, UserPreferences, UserProfile


class DjangoUsersDAO(UsersDAO):
    def get_or_create_profile(self, user: User) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": user.full_name},
        )
        return profile

    def get_or_create_preferences(self, user: User) -> UserPreferences:
        preferences, _ = UserPreferences.objects.get_or_create(user=user)
        return preferences
