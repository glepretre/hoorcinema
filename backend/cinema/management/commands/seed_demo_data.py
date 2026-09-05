import os
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cinema.models import AuthorRating, Favorite, Film, FilmRating
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP, ensure_role_groups

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
    help = "Create or update the demonstration users and role groups."

    def handle(self, *args, **options):
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

        with transaction.atomic():
            groups = ensure_role_groups()
            users = {}
            for user_data in DEMO_USERS:
                username = user_data["username"]
                defaults = {
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                    "is_staff": user_data.get("is_staff", False),
                    "is_superuser": user_data.get("is_superuser", False),
                }
                user = user_model.objects.filter(username=username).first()
                created = user is None
                if created:
                    user = user_model(username=username)
                elif user.email != user_data["email"]:
                    raise CommandError(
                        f"Refusing to overwrite existing user {username}"
                    )

                for field, value in defaults.items():
                    setattr(user, field, value)
                user.set_password(os.environ[user_data["password_env"]])
                user.save()

                group_name = user_data.get("group")
                if group_name:
                    user.groups.add(groups[group_name])
                users[username] = user

                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} {username}")

            films = (
                {
                    "title": "The Last Projection",
                    "description": "A projectionist prepares a cinema's final show.",
                    "release_date": date(2024, 10, 12),
                    "status": Film.Status.PUBLISHED,
                    "tmdb_vote_average": Decimal("7.40"),
                    "tmdb_vote_count": 128,
                },
                {
                    "title": "Midnight Rehearsal",
                    "description": "A film crew rehearses after the city goes quiet.",
                    "release_date": date(2025, 2, 8),
                    "status": Film.Status.DRAFT,
                    "tmdb_vote_average": None,
                    "tmdb_vote_count": 0,
                },
            )
            demo_films = []
            for film_data in films:
                matching_films = list(
                    Film.objects.filter(title=film_data["title"]).prefetch_related(
                        "authors"
                    )
                )
                film = matching_films[0] if len(matching_films) == 1 else None
                owned_by_seed = (
                    film is not None
                    and film.source == Film.Source.ADMIN
                    and users["demo_author"] in film.authors.all()
                )
                if matching_films and not owned_by_seed:
                    raise CommandError(
                        f"Refusing to overwrite existing film {film_data['title']}"
                    )
                created = film is None
                if created:
                    film = Film(title=film_data["title"])
                for field, value in film_data.items():
                    setattr(film, field, value)
                film.source = Film.Source.ADMIN
                film.save()
                film.authors.set([users["demo_author"]])
                demo_films.append(film)

                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} {film.title}")

            spectator = users["demo_spectator"]
            author = users["demo_author"]
            FilmRating.objects.update_or_create(
                spectator=spectator,
                film=demo_films[0],
                defaults={"score": 5},
            )
            AuthorRating.objects.update_or_create(
                spectator=spectator,
                author=author,
                defaults={"score": 4},
            )
            Favorite.objects.get_or_create(
                spectator=spectator,
                film=demo_films[0],
            )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
