from copy import deepcopy
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from cinema.models import Favorite, Film, FilmRating, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP, ensure_role_groups
from cinema.tmdb import TMDbError

MOVIE = {
    "id": 42,
    "title": "Remote Film",
    "overview": "Imported overview.",
    "release_date": "2025-04-12",
    "status": "Released",
    "vote_average": 8.126,
    "vote_count": 321,
    "poster_path": "/poster.jpg",
}
CREDITS = {
    "crew": [
        {
            "id": 84,
            "name": "Avery Director",
            "job": "Director",
            "profile_path": "/person.jpg",
        },
        {"id": 85, "name": "Sam Writer", "job": "Writer", "profile_path": None},
        {"id": 86, "name": "Casey Producer", "job": "Producer"},
        {"id": 84, "name": "Avery Director", "job": "Screenplay"},
    ]
}


class FakeClient:
    movies = [MOVIE]
    credits = {42: CREDITS}
    detail_error = None
    calls = []

    def __init__(self, token, timeout):
        assert token == "test-token"
        assert timeout == 10

    def get_popular_movies(self, *, page, language):
        self.calls.append(("list", page, language))
        return {"results": [{"id": movie["id"]} for movie in self.movies]}

    def get_movie_details(self, movie_id, *, language):
        self.calls.append(("details", movie_id, language))
        if self.detail_error:
            raise self.detail_error
        return deepcopy(next(movie for movie in self.movies if movie["id"] == movie_id))

    def get_movie_credits(self, movie_id, *, language):
        self.calls.append(("credits", movie_id, language))
        return deepcopy(self.credits[movie_id])


@pytest.fixture(autouse=True)
def configure_client(monkeypatch):
    FakeClient.movies = [MOVIE]
    FakeClient.credits = {42: CREDITS}
    FakeClient.detail_error = None
    FakeClient.calls = []
    monkeypatch.setenv("TMDB_API_TOKEN", "test-token")
    monkeypatch.setattr("cinema.management.commands.import_tmdb.TMDbClient", FakeClient)


@pytest.mark.django_db
def test_import_tmdb_creates_films_and_authors():
    stdout = StringIO()

    call_command("import_tmdb", limit=1, page=3, language="fr-FR", stdout=stdout)

    film = Film.objects.get(tmdb_id=42)
    assert film.title == "Remote Film"
    assert film.description == "Imported overview."
    assert str(film.release_date) == "2025-04-12"
    assert str(film.tmdb_vote_average) == "8.13"
    assert film.tmdb_vote_count == 321
    assert film.status == Film.Status.RELEASED
    assert film.source == Film.Source.TMDB
    assert set(film.authors.values_list("tmdb_id", flat=True)) == {84, 85}
    director = User.objects.get(tmdb_id=84)
    assert director.first_name == "Avery Director"
    assert director.avatar == "https://image.tmdb.org/t/p/w500/person.jpg"
    assert not director.has_usable_password()
    assert director.groups.filter(name=AUTHOR_GROUP).exists()
    assert FakeClient.calls[0] == ("list", 3, "fr-FR")
    assert "created=1, updated=0, skipped=0, failed=0" in stdout.getvalue()


@pytest.mark.django_db
def test_import_tmdb_defaults_to_french_and_falls_back_field_by_field(monkeypatch):
    french_movie = {**MOVIE, "title": "Film distant", "overview": ""}
    english_movie = {**MOVIE, "title": "Remote Film", "overview": "English overview."}

    def get_movie_details(self, movie_id, *, language):
        self.calls.append(("details", movie_id, language))
        return deepcopy(french_movie if language == "fr-FR" else english_movie)

    monkeypatch.setattr(FakeClient, "get_movie_details", get_movie_details)

    call_command("import_tmdb")

    film = Film.objects.get(tmdb_id=42)
    assert film.title == "Film distant"
    assert film.description == "English overview."
    assert ("list", 1, "fr-FR") in FakeClient.calls
    assert ("details", 42, "fr-FR") in FakeClient.calls
    assert ("details", 42, "en-US") in FakeClient.calls
    assert ("credits", 42, "fr-FR") in FakeClient.calls


@pytest.mark.django_db
def test_import_tmdb_is_idempotent_and_preserves_local_data():
    call_command("import_tmdb")
    film = Film.objects.get(tmdb_id=42)
    groups = ensure_role_groups()
    spectator = User.objects.create_user(username="viewer", password="safe-password")
    spectator.groups.add(groups[SPECTATOR_GROUP])
    FilmRating.objects.create(spectator=spectator, film=film, score=5)
    Favorite.objects.create(spectator=spectator, film=film)
    FakeClient.movies[0] = {**MOVIE, "title": "Updated Remote Film", "vote_count": 400}
    stdout = StringIO()

    call_command("import_tmdb", stdout=stdout)

    film.refresh_from_db()
    assert film.title == "Updated Remote Film"
    assert film.tmdb_vote_count == 400
    assert Film.objects.count() == 1
    assert User.objects.filter(source=User.Source.TMDB).count() == 2
    assert FilmRating.objects.get(film=film).score == 5
    assert Favorite.objects.filter(film=film, spectator=spectator).exists()
    assert "created=0, updated=1, skipped=0, failed=0" in stdout.getvalue()


@pytest.mark.django_db
def test_import_tmdb_accepts_partial_data_and_ignores_other_crew():
    FakeClient.movies[0] = {
        "id": 42,
        "title": "Partial Film",
        "release_date": "unknown",
        "vote_average": None,
        "vote_count": -1,
    }

    call_command("import_tmdb")

    assert Film.objects.get(tmdb_id=42).status == Film.Status.PLANNED

    film = Film.objects.get(tmdb_id=42)
    assert film.description == ""
    assert film.release_date is None
    assert film.tmdb_vote_average is None
    assert film.tmdb_vote_count == 0
    assert set(film.authors.values_list("tmdb_id", flat=True)) == {84, 85}


@pytest.mark.django_db
def test_import_tmdb_dry_run_rolls_back_changes():
    stdout = StringIO()

    call_command("import_tmdb", dry_run=True, stdout=stdout)

    assert not Film.objects.exists()
    assert not User.objects.filter(source=User.Source.TMDB).exists()
    assert "Dry run: TMDb import complete: created=1" in stdout.getvalue()


@pytest.mark.django_db
def test_import_tmdb_reports_remote_failure_and_continues():
    FakeClient.detail_error = TMDbError("TMDb timed out while requesting a movie.")
    stdout = StringIO()
    stderr = StringIO()

    call_command("import_tmdb", stdout=stdout, stderr=stderr)

    assert not Film.objects.exists()
    assert "failed=1" in stdout.getvalue()
    assert "Failed movie 42" in stderr.getvalue()


@pytest.mark.django_db
def test_import_tmdb_rejects_unknown_movie_status():
    FakeClient.movies[0] = {**MOVIE, "status": "Unknown"}
    stdout = StringIO()
    stderr = StringIO()

    call_command("import_tmdb", stdout=stdout, stderr=stderr)

    assert not Film.objects.exists()
    assert "failed=1" in stdout.getvalue()
    assert "invalid movie status" in stderr.getvalue()


@pytest.mark.django_db
def test_import_tmdb_refuses_local_identifier_collision():
    Film.objects.create(title="Local Film", tmdb_id=42, source=Film.Source.ADMIN)
    stdout = StringIO()
    stderr = StringIO()

    call_command("import_tmdb", stdout=stdout, stderr=stderr)

    assert Film.objects.get(tmdb_id=42).title == "Local Film"
    assert "failed=1" in stdout.getvalue()
    assert "refusing to overwrite local film" in stderr.getvalue()


@pytest.mark.django_db
def test_import_tmdb_reports_case_insensitive_author_username_collision():
    User.objects.create_user(username="TMDB_84")
    stdout = StringIO()
    stderr = StringIO()

    call_command("import_tmdb", stdout=stdout, stderr=stderr)

    assert not Film.objects.exists()
    assert "failed=1" in stdout.getvalue()
    assert "username tmdb_84 is already in use" in stderr.getvalue()


@pytest.mark.django_db
def test_import_tmdb_can_import_one_movie_without_listing():
    call_command("import_tmdb", movie_id=42)

    assert Film.objects.filter(tmdb_id=42).exists()
    assert all(call[0] != "list" for call in FakeClient.calls)


@pytest.mark.django_db
def test_import_tmdb_can_import_multiple_movie_ids_without_listing():
    second_movie = {**MOVIE, "id": 43, "title": "Second Remote Film"}
    FakeClient.movies = [MOVIE, second_movie]
    FakeClient.credits[43] = {"crew": []}

    call_command("import_tmdb", movie_id=[42, 43])

    assert set(Film.objects.values_list("tmdb_id", flat=True)) == {42, 43}
    assert all(call[0] != "list" for call in FakeClient.calls)


@pytest.mark.django_db
def test_import_tmdb_requires_token(monkeypatch):
    monkeypatch.delenv("TMDB_API_TOKEN")

    with pytest.raises(CommandError, match="TMDB_API_TOKEN"):
        call_command("import_tmdb")
