import os
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cinema.demo_catalogue import AUTHORS, FILMS
from cinema.models import AuthorRating, Favorite, Film, FilmRating
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP, ensure_role_groups

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
DEMO_USERS = (
    {
        "username": "demo_author",
        "email": "author@example.com",
        "first_name": "Demo",
        "last_name": "Author",
        "password_env": "DEMO_AUTHOR_PASSWORD",
        "group": AUTHOR_GROUP,
    },
    {
        "username": "demo_spectator",
        "email": "spectator@example.com",
        "first_name": "Demo",
        "last_name": "Spectator",
        "password_env": "DEMO_SPECTATOR_PASSWORD",
        "group": SPECTATOR_GROUP,
    },
    {
        "username": "demo_admin",
        "email": "admin@example.com",
        "first_name": "Demo",
        "last_name": "Administrator",
        "password_env": "DEMO_ADMIN_PASSWORD",
        "is_staff": True,
        "is_superuser": True,
    },
)


class Command(BaseCommand):
    help = "Create or update the reproducible demonstration catalogue and users."

    def handle(self, *args, **options):
        self._validate_passwords()

        with transaction.atomic():
            groups = ensure_role_groups()
            users = self._upsert_demo_users(groups)
            self._validate_catalogue_collisions()
            authors = self._upsert_authors(groups[AUTHOR_GROUP])
            films = self._upsert_films(authors)
            self._remove_stale_data()
            self._upsert_sample_activity(users, films[0])

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    @staticmethod
    def _validate_passwords():
        missing_variables = [
            user["password_env"]
            for user in DEMO_USERS
            if not os.getenv(user["password_env"])
        ]
        if missing_variables:
            names = ", ".join(missing_variables)
            raise CommandError(f"Missing required environment variables: {names}")

        user_model = get_user_model()
        for user_data in DEMO_USERS:
            candidate = user_model(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
            try:
                validate_password(os.environ[user_data["password_env"]], user=candidate)
            except ValidationError as error:
                messages = " ".join(error.messages)
                raise CommandError(
                    f"Invalid password for {user_data['username']}: {messages}"
                ) from error

    def _upsert_demo_users(self, groups):
        user_model = get_user_model()
        users = {}
        for user_data in DEMO_USERS:
            username = user_data["username"]
            user = user_model.objects.filter(username=username).first()
            created = user is None
            if created:
                user = user_model(username=username)
            elif (
                user.email != user_data["email"]
                or user.source != user_model.Source.ADMIN
            ):
                raise CommandError(f"Refusing to overwrite existing user {username}")

            for field in ("email", "first_name", "last_name"):
                setattr(user, field, user_data[field])
            user.is_active = True
            user.is_staff = user_data.get("is_staff", False)
            user.is_superuser = user_data.get("is_superuser", False)
            user.source = user_model.Source.ADMIN
            user.tmdb_id = None
            user.set_password(os.environ[user_data["password_env"]])
            user.save()

            group_name = user_data.get("group")
            if group_name:
                user.groups.add(groups[group_name])
            users[username] = user
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} {username}")
        return users

    @staticmethod
    def _validate_catalogue_collisions():
        user_model = get_user_model()
        for tmdb_id in AUTHORS:
            user = user_model.objects.filter(tmdb_id=tmdb_id).first()
            if user and user.source != user_model.Source.TMDB:
                raise CommandError(
                    f"Refusing to overwrite local user with TMDB ID {tmdb_id}"
                )
            username = f"tmdb_{tmdb_id}"
            username_owner = user_model.objects.filter(username=username).first()
            if username_owner and username_owner != user:
                raise CommandError(f"Refusing to overwrite existing user {username}")

        for film_data in FILMS:
            film = Film.objects.filter(tmdb_id=film_data["tmdb_id"]).first()
            if film and film.source != Film.Source.TMDB:
                raise CommandError(
                    "Refusing to overwrite local film with TMDB ID "
                    f"{film_data['tmdb_id']}"
                )

    @staticmethod
    def _upsert_authors(author_group):
        user_model = get_user_model()
        authors = {}
        for tmdb_id, (name, avatar_path) in AUTHORS.items():
            user = user_model.objects.filter(tmdb_id=tmdb_id).first()
            if user is None:
                user = user_model(tmdb_id=tmdb_id)
            user.username = f"tmdb_{tmdb_id}"
            user.email = ""
            user.first_name = name
            user.last_name = ""
            user.bio = ""
            user.avatar = f"{IMAGE_BASE_URL}{avatar_path}" if avatar_path else ""
            user.source = user_model.Source.TMDB
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.set_unusable_password()
            user.full_clean(exclude=("groups", "user_permissions"))
            user.save()
            user.groups.add(author_group)
            authors[tmdb_id] = user
        return authors

    @staticmethod
    def _upsert_films(authors):
        films = []
        for film_data in FILMS:
            tmdb_id = film_data["tmdb_id"]
            film = Film.objects.filter(tmdb_id=tmdb_id).first() or Film(tmdb_id=tmdb_id)
            for field in (
                "title",
                "description",
                "status",
                "tmdb_vote_count",
                "poster_path",
            ):
                setattr(film, field, film_data[field])
            film.release_date = date.fromisoformat(film_data["release_date"])
            film.is_archived = False
            film.source = Film.Source.TMDB
            film.tmdb_vote_average = Decimal(film_data["tmdb_vote_average"])
            film.full_clean(exclude=("authors",))
            film.save()
            film.authors.set(authors[tmdb_id] for tmdb_id in film_data["authors"])
            films.append(film)
        return films

    @staticmethod
    def _remove_stale_data():
        catalogue_ids = [film["tmdb_id"] for film in FILMS]
        Film.objects.filter(source=Film.Source.TMDB).exclude(
            tmdb_id__in=catalogue_ids
        ).delete()

        user_model = get_user_model()
        user_model.objects.filter(
            source=user_model.Source.TMDB,
            authored_films__isnull=True,
        ).delete()

    @staticmethod
    def _upsert_sample_activity(users, film):
        spectator = users["demo_spectator"]
        author = users["demo_author"]
        FilmRating.objects.update_or_create(
            spectator=spectator,
            film=film,
            defaults={"score": 5},
        )
        AuthorRating.objects.update_or_create(
            spectator=spectator,
            author=author,
            defaults={"score": 4},
        )
        Favorite.objects.get_or_create(spectator=spectator, film=film)
