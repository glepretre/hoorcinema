from django.contrib.auth.models import AbstractUser
from django.db import models

from cinema.managers import AuthorManager, SpectatorManager


class User(AbstractUser):
    class Source(models.TextChoices):
        ADMIN = "ADMIN", "Administration"
        TMDB = "TMDB", "TMDb"

    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    avatar = models.URLField(blank=True, max_length=500)
    source = models.CharField(
        choices=Source.choices,
        db_index=True,
        default=Source.ADMIN,
        max_length=10,
    )
    tmdb_id = models.PositiveBigIntegerField(blank=True, null=True, unique=True)


class Author(User):
    objects = AuthorManager()

    class Meta:
        proxy = True
        ordering = ("last_name", "first_name", "username")


class Spectator(User):
    objects = SpectatorManager()

    class Meta:
        proxy = True
        ordering = ("last_name", "first_name", "username")
