from django.contrib.auth.models import UserManager

from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


class CinemaUserManager(UserManager):
    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})


class AuthorManager(CinemaUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(groups__name=AUTHOR_GROUP)


class SpectatorManager(CinemaUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(groups__name=SPECTATOR_GROUP)
