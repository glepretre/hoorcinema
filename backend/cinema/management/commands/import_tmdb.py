import os
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cinema.models import Film
from cinema.roles import AUTHOR_GROUP, ensure_role_groups
from cinema.tmdb import TMDbClient, TMDbError

AUTHOR_JOBS = {"Director", "Screenplay", "Writer"}
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
DEFAULT_LANGUAGE = "fr-FR"
FALLBACK_LANGUAGE = "en-US"
LOCALIZED_DETAIL_FIELDS = ("title", "overview")


def positive_integer(value):
    try:
        number = int(value)
    except ValueError as error:
        raise CommandError("Values must be positive integers.") from error
    if number < 1:
        raise CommandError("Values must be positive integers.")
    return number


class ImportCollisionError(Exception):
    pass


class Command(BaseCommand):
    help = "Import popular films, directors, and writers from TMDb."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=positive_integer, default=20)
        parser.add_argument("--page", type=positive_integer, default=1)
        parser.add_argument("--movie-id", type=positive_integer)
        parser.add_argument("--language", default=DEFAULT_LANGUAGE)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        token = os.getenv("TMDB_API_TOKEN")
        if not token:
            raise CommandError("Missing required environment variable: TMDB_API_TOKEN")

        client = TMDbClient(token, timeout=10)
        counts = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
        movie_id = options["movie_id"]
        if movie_id:
            movie_ids = [movie_id]
        else:
            try:
                payload = client.get_popular_movies(
                    page=options["page"], language=options["language"]
                )
            except TMDbError as error:
                raise CommandError(str(error)) from error
            results = payload.get("results")
            if not isinstance(results, list):
                raise CommandError("TMDb returned an invalid movie list.")
            movie_ids = []
            for item in results[: options["limit"]]:
                item_id = item.get("id") if isinstance(item, dict) else None
                if isinstance(item_id, int) and item_id > 0:
                    movie_ids.append(item_id)
                else:
                    counts["skipped"] += 1

        for current_movie_id in movie_ids:
            try:
                details = self._get_movie_details(
                    client, current_movie_id, language=options["language"]
                )
                credits = client.get_movie_credits(
                    current_movie_id, language=options["language"]
                )
                action = self._import_movie(details, credits, options["dry_run"])
            except (TMDbError, ImportCollisionError) as error:
                counts["failed"] += 1
                self.stderr.write(f"Failed movie {current_movie_id}: {error}")
                continue
            counts[action] += 1

        prefix = "Dry run: " if options["dry_run"] else ""
        summary = ", ".join(f"{name}={count}" for name, count in counts.items())
        self.stdout.write(
            self.style.SUCCESS(f"{prefix}TMDb import complete: {summary}.")
        )

    @staticmethod
    def _get_movie_details(client, movie_id, *, language):
        details = client.get_movie_details(movie_id, language=language)
        if language == FALLBACK_LANGUAGE or not isinstance(details, dict):
            return details
        if all(details.get(field) for field in LOCALIZED_DETAIL_FIELDS):
            return details

        fallback = client.get_movie_details(movie_id, language=FALLBACK_LANGUAGE)
        if not isinstance(fallback, dict):
            raise TMDbError("TMDb returned invalid fallback movie data.")

        merged = fallback.copy()
        merged.update(
            {
                key: value
                for key, value in details.items()
                if value is not None and (not isinstance(value, str) or value.strip())
            }
        )
        return merged

    def _import_movie(self, details, credits, dry_run):
        if not isinstance(details, dict) or not isinstance(credits, dict):
            raise TMDbError("TMDb returned invalid movie data.")
        tmdb_id = details.get("id")
        title = details.get("title")
        if (
            not isinstance(tmdb_id, int)
            or tmdb_id < 1
            or not isinstance(title, str)
            or not title.strip()
        ):
            return "skipped"

        with transaction.atomic():
            existing = Film.objects.filter(tmdb_id=tmdb_id).first()
            if existing and existing.source != Film.Source.TMDB:
                raise ImportCollisionError(
                    f"refusing to overwrite local film with TMDb ID {tmdb_id}"
                )
            film = existing or Film(tmdb_id=tmdb_id)
            created = existing is None
            film.title = title.strip()[:255]
            film.description = str(details.get("overview") or "")
            film.release_date = self._parse_date(details.get("release_date"))
            film.status = self._status(details.get("status"))
            film.source = Film.Source.TMDB
            film.tmdb_vote_average = self._parse_vote(details.get("vote_average"))
            vote_count = details.get("vote_count")
            film.tmdb_vote_count = (
                vote_count if isinstance(vote_count, int) and vote_count >= 0 else 0
            )
            film.poster_path = str(details.get("poster_path") or "")[:500]
            film.full_clean(exclude=("authors",))
            film.save()

            author_group = ensure_role_groups()[AUTHOR_GROUP]
            authors = [
                self._import_author(person, author_group)
                for person in self._authors(credits)
            ]
            film.authors.set(authors)
            if dry_run:
                transaction.set_rollback(True)
            return "created" if created else "updated"

    @staticmethod
    def _status(value):
        if value in (None, ""):
            return Film.Status.PLANNED
        if value not in Film.Status.values:
            raise TMDbError("TMDb returned an invalid movie status.")
        return value

    @staticmethod
    def _authors(credits):
        crew = credits.get("crew", [])
        if not isinstance(crew, list):
            return []
        authors = {}
        for person in crew:
            if (
                isinstance(person, dict)
                and isinstance(person.get("id"), int)
                and person["id"] > 0
                and (
                    person.get("job") in AUTHOR_JOBS
                    or person.get("department") == "Writing"
                )
            ):
                authors.setdefault(person["id"], person)
        return authors.values()

    @staticmethod
    def _import_author(person, author_group):
        user_model = get_user_model()
        tmdb_id = person["id"]
        username = f"tmdb_{tmdb_id}"
        user = user_model.objects.filter(tmdb_id=tmdb_id).first()
        if user and user.source != user_model.Source.TMDB:
            raise ImportCollisionError(
                f"refusing to overwrite local user with TMDb ID {tmdb_id}"
            )
        username_owner = user_model.objects.filter(username=username).first()
        if username_owner and username_owner != user:
            raise ImportCollisionError(f"username {username} is already in use")
        if user is None:
            user = user_model(username=username, tmdb_id=tmdb_id)
            user.set_unusable_password()

        name = str(person.get("name") or username).strip()
        user.username = username
        user.first_name = name[:150]
        user.last_name = ""
        user.source = user_model.Source.TMDB
        profile_path = person.get("profile_path")
        user.avatar = f"{IMAGE_BASE_URL}{profile_path}"[:500] if profile_path else ""
        user.full_clean(exclude=("groups", "user_permissions"))
        user.save()
        user.groups.add(author_group)
        return user

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_vote(value):
        if value is None:
            return None
        try:
            vote = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return None
        return vote if Decimal("0") <= vote <= Decimal("10") else None
