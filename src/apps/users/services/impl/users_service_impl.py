from apps.users.daos.interface.users_dao_interface import UsersDAO
from apps.users.models import User, UserPreferences, UserProfile
from apps.users.services.interface.users_service_interface import UsersServiceInterface


class UsersServiceImpl(UsersServiceInterface):
    def __init__(self, dao: UsersDAO) -> None:
        self._dao = dao

    def get_profile(self, user: User) -> UserProfile:
        return self._dao.get_or_create_profile(user)

    def get_preferences(self, user: User) -> UserPreferences:
        return self._dao.get_or_create_preferences(user)
