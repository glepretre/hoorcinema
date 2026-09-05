from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from cinema.managers import AuthorManager, SpectatorManager
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


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


class RatingScore(models.IntegerChoices):
    ONE = 1, "1"
    TWO = 2, "2"
    THREE = 3, "3"
    FOUR = 4, "4"
    FIVE = 5, "5"


class Film(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    class Source(models.TextChoices):
        ADMIN = "ADMIN", "Administration"
        TMDB = "TMDB", "TMDb"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_date = models.DateField(blank=True, db_index=True, null=True)
    status = models.CharField(
        choices=Status.choices,
        db_index=True,
        default=Status.DRAFT,
        max_length=10,
    )
    authors = models.ManyToManyField(
        User,
        blank=True,
        limit_choices_to={"groups__name": AUTHOR_GROUP},
        related_name="authored_films",
        through="FilmAuthorship",
    )
    source = models.CharField(
        choices=Source.choices,
        db_index=True,
        default=Source.ADMIN,
        max_length=10,
    )
    tmdb_id = models.PositiveBigIntegerField(blank=True, null=True, unique=True)
    tmdb_vote_average = models.DecimalField(
        blank=True,
        decimal_places=2,
        max_digits=4,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    tmdb_vote_count = models.PositiveIntegerField(default=0)
    poster_path = models.CharField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title", "pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=("DRAFT", "PUBLISHED", "ARCHIVED")),
                name="film_valid_status",
            ),
            models.CheckConstraint(
                condition=models.Q(source__in=("ADMIN", "TMDB")),
                name="film_valid_source",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(tmdb_vote_average__isnull=True)
                    | models.Q(tmdb_vote_average__gte=0, tmdb_vote_average__lte=10)
                ),
                name="film_valid_tmdb_vote_average",
            ),
        ]

    def __str__(self):
        return self.title


def validate_user_role(user, group_name, field_name):
    if user.pk and not user.groups.filter(name=group_name).exists():
        raise ValidationError({field_name: f"User must have the {group_name} role."})


class FilmAuthorship(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("film", "author"),
                name="unique_film_author",
            )
        ]

    def clean(self):
        super().clean()
        validate_user_role(self.author, AUTHOR_GROUP, "author")


class FilmRating(models.Model):
    spectator = models.ForeignKey(
        User,
        limit_choices_to={"groups__name": SPECTATOR_GROUP},
        on_delete=models.CASCADE,
        related_name="film_ratings",
    )
    film = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    score = models.PositiveSmallIntegerField(
        choices=RatingScore.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("spectator", "film"),
                name="unique_spectator_film_rating",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=1, score__lte=5),
                name="film_rating_score_between_1_and_5",
            ),
        ]

    def clean(self):
        super().clean()
        validate_user_role(self.spectator, SPECTATOR_GROUP, "spectator")


class AuthorRating(models.Model):
    spectator = models.ForeignKey(
        User,
        limit_choices_to={"groups__name": SPECTATOR_GROUP},
        on_delete=models.CASCADE,
        related_name="author_ratings_given",
    )
    author = models.ForeignKey(
        User,
        limit_choices_to={"groups__name": AUTHOR_GROUP},
        on_delete=models.CASCADE,
        related_name="author_ratings_received",
    )
    score = models.PositiveSmallIntegerField(
        choices=RatingScore.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("spectator", "author"),
                name="unique_spectator_author_rating",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=1, score__lte=5),
                name="author_rating_score_between_1_and_5",
            ),
        ]

    def clean(self):
        super().clean()
        validate_user_role(self.spectator, SPECTATOR_GROUP, "spectator")
        validate_user_role(self.author, AUTHOR_GROUP, "author")


class Favorite(models.Model):
    spectator = models.ForeignKey(
        User,
        limit_choices_to={"groups__name": SPECTATOR_GROUP},
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    film = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("spectator", "film"),
                name="unique_spectator_favorite",
            )
        ]

    def clean(self):
        super().clean()
        validate_user_role(self.spectator, SPECTATOR_GROUP, "spectator")


@receiver(m2m_changed, sender=Film.authors.through)
def validate_film_authors(sender, instance, action, reverse, pk_set, **kwargs):
    if action != "pre_add":
        return
    if reverse:
        validate_user_role(instance, AUTHOR_GROUP, "author")
    elif User.objects.filter(pk__in=pk_set).exclude(groups__name=AUTHOR_GROUP).exists():
        raise ValidationError({"authors": f"Users must have the {AUTHOR_GROUP} role."})
