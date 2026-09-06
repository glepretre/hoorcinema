import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

from cinema.demo_catalogue import AUTHORS
from cinema.management.commands.seed_demo_data import Command
from cinema.models import AuthorRating, Favorite, Film, FilmRating, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP

PASSWORDS = {
    "DEMO_AUTHOR_PASSWORD": "author-test-password",
    "DEMO_SPECTATOR_PASSWORD": "spectator-test-password",
    "DEMO_ADMIN_PASSWORD": "admin-test-password",
}
EXPECTED_FILMS = {
    122: "Le Seigneur des anneaux : Le Retour du roi",
    671: "Harry Potter a l'ecole des sorciers",
    672: "Harry Potter et la Chambre des secrets",
    673: "Harry Potter et le Prisonnier d'Azkaban",
    674: "Harry Potter et la Coupe de feu",
    675: "Harry Potter et l'Ordre du Phenix",
    767: "Harry Potter et le Prince de sang-mele",
    920: "Cars : Quatre roues",
    1726: "Iron Man",
    12444: "Harry Potter et les Reliques de la Mort - 1ere partie",
    12445: "Harry Potter et les Reliques de la Mort - 2eme partie",
    23629: "Sucker Punch",
    96721: "Rush",
    157350: "Divergente",
    293310: "Citizenfour",
    299534: "Avengers : Endgame",
    318846: "The Big Short : Le Casse du Siecle",
    911430: "F1 Le Film",
}


@pytest.fixture
def demo_passwords(monkeypatch):
    for name, password in PASSWORDS.items():
        monkeypatch.setenv(name, password)


def normalized_title(title):
    return (
        title.replace("\u00a0", " ")
        .replace("\u00e0", "a")
        .replace("\u00e9", "e")
        .replace("\u00e8", "e")
        .replace("\u00ea", "e")
        .replace("\u00ae", "")
    )


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent(demo_passwords):
    call_command("seed_demo_data")
    call_command("seed_demo_data")

    assert User.objects.filter(username__startswith="demo_").count() == 3
    author = User.objects.get(username="demo_author")
    spectator = User.objects.get(username="demo_spectator")
    administrator = User.objects.get(username="demo_admin")

    assert author.groups.get().name == AUTHOR_GROUP
    assert not author.authored_films.exists()
    assert spectator.groups.get().name == SPECTATOR_GROUP
    assert author.check_password(PASSWORDS["DEMO_AUTHOR_PASSWORD"])
    assert spectator.check_password(PASSWORDS["DEMO_SPECTATOR_PASSWORD"])
    assert administrator.check_password(PASSWORDS["DEMO_ADMIN_PASSWORD"])
    assert administrator.is_staff
    assert administrator.is_superuser
    assert Group.objects.filter(name__in=[AUTHOR_GROUP, SPECTATOR_GROUP]).count() == 2

    films = Film.objects.filter(source=Film.Source.TMDB)
    assert films.count() == 18
    assert {
        film.tmdb_id: normalized_title(film.title) for film in films
    } == EXPECTED_FILMS

    linked_authors = User.objects.filter(authored_films__in=films).distinct()
    assert linked_authors.count() == 58
    assert set(linked_authors.values_list("tmdb_id", flat=True)) == set(AUTHORS)
    assert all(not user.has_usable_password() for user in linked_authors)
    assert all(
        user.source == User.Source.TMDB
        and user.groups.filter(name=AUTHOR_GROUP).exists()
        for user in linked_authors
    )

    sample_film = films.get(tmdb_id=122)
    assert FilmRating.objects.get(spectator=spectator, film=sample_film).score == 5
    assert AuthorRating.objects.get(spectator=spectator, author=author).score == 4
    assert Favorite.objects.filter(spectator=spectator, film=sample_film).count() == 1


@pytest.mark.django_db
def test_seed_prunes_stale_tmdb_data(demo_passwords):
    call_command("seed_demo_data")
    stale_author = User.objects.create(
        username="tmdb_999001",
        tmdb_id=999001,
        source=User.Source.TMDB,
    )
    stale_author.groups.add(Group.objects.get(name=AUTHOR_GROUP))
    stale_film = Film.objects.create(
        title="Stale import",
        source=Film.Source.TMDB,
        tmdb_id=999002,
    )
    stale_film.authors.add(stale_author)
    orphan = User.objects.create(
        username="tmdb_999003",
        tmdb_id=999003,
        source=User.Source.TMDB,
    )
    local_film = Film.objects.create(title="Local film")
    local_user = User.objects.create_user(
        username="local_user", password="safe-password"
    )

    call_command("seed_demo_data")

    assert not Film.objects.filter(pk=stale_film.pk).exists()
    assert not User.objects.filter(pk__in=[stale_author.pk, orphan.pk]).exists()
    assert Film.objects.filter(pk=local_film.pk).exists()
    assert User.objects.filter(pk=local_user.pk).exists()
    assert (
        User.objects.get(username="demo_author")
        .groups.filter(name=AUTHOR_GROUP)
        .exists()
    )


@pytest.mark.django_db
def test_seed_demo_data_requires_all_passwords(monkeypatch):
    for name in PASSWORDS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(CommandError, match="DEMO_AUTHOR_PASSWORD"):
        call_command("seed_demo_data")

    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
def test_seed_demo_data_rejects_weak_passwords(monkeypatch):
    for name in PASSWORDS:
        monkeypatch.setenv(name, "short")

    with pytest.raises(CommandError, match="Invalid password for demo_author"):
        call_command("seed_demo_data")

    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
def test_seed_demo_data_refuses_demo_username_collisions(demo_passwords):
    existing_user = User.objects.create_user(
        username="demo_author",
        email="real-user@example.com",
        password="original-secure-password",
    )

    with pytest.raises(CommandError, match="Refusing to overwrite"):
        call_command("seed_demo_data")

    existing_user.refresh_from_db()
    assert existing_user.email == "real-user@example.com"
    assert existing_user.check_password("original-secure-password")
    assert not User.objects.filter(username="demo_spectator").exists()


@pytest.mark.django_db
def test_seed_demo_data_refuses_tmdb_film_id_collisions(demo_passwords):
    existing_film = Film.objects.create(
        title="Local production",
        description="Existing production data.",
        tmdb_id=122,
        source=Film.Source.ADMIN,
    )

    with pytest.raises(CommandError, match="local film with TMDB ID 122"):
        call_command("seed_demo_data")

    existing_film.refresh_from_db()
    assert existing_film.description == "Existing production data."
    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "existing_user",
    (
        {"username": "local", "tmdb_id": 108},
        {"username": "tmdb_108", "tmdb_id": None},
    ),
)
def test_seed_demo_data_refuses_tmdb_author_collisions(demo_passwords, existing_user):
    user = User.objects.create_user(
        **existing_user,
        email="local@example.com",
        password="original-secure-password",
    )

    with pytest.raises(CommandError, match="Refusing to overwrite"):
        call_command("seed_demo_data")

    user.refresh_from_db()
    assert user.source == User.Source.ADMIN
    assert user.check_password("original-secure-password")
    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
def test_seed_demo_data_rolls_back_late_failures(demo_passwords, monkeypatch):
    original_group_ids = set(Group.objects.values_list("pk", flat=True))

    def fail(*args):
        raise RuntimeError("late seed failure")

    monkeypatch.setattr(Command, "_upsert_sample_activity", fail)

    with pytest.raises(RuntimeError, match="late seed failure"):
        call_command("seed_demo_data")

    assert not User.objects.exists()
    assert not Film.objects.exists()
    assert set(Group.objects.values_list("pk", flat=True)) == original_group_ids
