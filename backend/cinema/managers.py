from django.contrib.auth.models import UserManager

from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


class AuthorManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(groups__name=AUTHOR_GROUP)


class SpectatorManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(groups__name=SPECTATOR_GROUP)
