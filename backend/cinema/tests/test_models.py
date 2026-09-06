from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Avg
from django.db.models.deletion import ProtectedError

from cinema.models import AuthorRating, Favorite, Film, FilmRating, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


@pytest.fixture
def author(db):
    user = User.objects.create_user(username="film_author")
    user.groups.add(Group.objects.get(name=AUTHOR_GROUP))
    return user


@pytest.fixture
def spectator(db):
    user = User.objects.create_user(username="film_spectator")
    user.groups.add(Group.objects.get(name=SPECTATOR_GROUP))
    return user


@pytest.fixture
def film(db, author):
    instance = Film.objects.create(
        title="Northern Lights",
        description="A journey beyond the Arctic Circle.",
        status=Film.Status.RELEASED,
    )
    instance.authors.add(author)
    return instance


@pytest.mark.django_db
def test_film_choices_defaults_indexes_and_authors(author):
    film = Film.objects.create(title="First Feature")
    film.authors.add(author)

    assert film.status == Film.Status.PLANNED
    assert film.is_archived is False
    assert film.source == Film.Source.ADMIN
    assert film.tmdb_vote_average is None
    assert film.tmdb_vote_count == 0
    assert list(film.authors.all()) == [author]
    assert str(film) == "First Feature"
    assert set(Film.Status.values) == {
        "Rumored",
        "Planned",
        "In Production",
        "Post Production",
        "Released",
        "Canceled",
    }
    assert set(Film.Source.values) == {"ADMIN", "TMDB"}
    assert all(
        Film._meta.get_field(field_name).db_index
        for field_name in (
            "status",
            "source",
            "release_date",
            "is_archived",
            "created_at",
        )
    )
    assert Film._meta.get_field("tmdb_id").unique


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "INVALID"),
        ("source", "INVALID"),
        ("tmdb_vote_average", Decimal("-0.01")),
        ("tmdb_vote_average", Decimal("10.01")),
        ("tmdb_vote_count", -1),
    ],
)
def test_film_database_constraints(field, value):
    with pytest.raises(IntegrityError), transaction.atomic():
        Film.objects.create(title="Invalid Film", **{field: value})


@pytest.mark.django_db
def test_rating_and_favorite_uniqueness(film, spectator, author):
    FilmRating.objects.create(film=film, spectator=spectator, score=4)
    AuthorRating.objects.create(author=author, spectator=spectator, score=5)
    Favorite.objects.create(film=film, spectator=spectator)

    with pytest.raises(IntegrityError), transaction.atomic():
        FilmRating.objects.create(film=film, spectator=spectator, score=3)
    with pytest.raises(IntegrityError), transaction.atomic():
        AuthorRating.objects.create(author=author, spectator=spectator, score=3)
    with pytest.raises(IntegrityError), transaction.atomic():
        Favorite.objects.create(film=film, spectator=spectator)


@pytest.mark.django_db
def test_tmdb_id_is_unique():
    Film.objects.create(title="Remote Film", source=Film.Source.TMDB, tmdb_id=42)

    with pytest.raises(IntegrityError), transaction.atomic():
        Film.objects.create(title="Duplicate Remote Film", tmdb_id=42)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model", "relations"), [(FilmRating, "film"), (AuthorRating, "author")]
)
def test_rating_score_database_constraint(model, relations, film, spectator, author):
    related_object = film if relations == "film" else author

    with pytest.raises(IntegrityError), transaction.atomic():
        model.objects.create(
            spectator=spectator,
            score=0,
            **{relations: related_object},
        )


@pytest.mark.django_db
def test_role_dependent_relations_validate_application_boundaries(
    film, spectator, author
):
    user_without_role = User.objects.create_user(username="without_role")

    with pytest.raises(ValidationError, match="SPECTATOR"):
        FilmRating(film=film, spectator=user_without_role, score=3).full_clean()
    with pytest.raises(ValidationError, match="SPECTATOR"):
        Favorite(film=film, spectator=user_without_role).full_clean()
    with pytest.raises(ValidationError, match="AUTHOR"):
        AuthorRating(
            author=user_without_role,
            spectator=spectator,
            score=3,
        ).full_clean()

    FilmRating(film=film, spectator=spectator, score=3).full_clean()
    AuthorRating(author=author, spectator=spectator, score=3).full_clean()
    Favorite(film=film, spectator=spectator).full_clean()


@pytest.mark.django_db
def test_adding_a_film_author_requires_author_role():
    film = Film.objects.create(title="Role Bound Film")
    user_without_role = User.objects.create_user(username="not_an_author")

    with pytest.raises(ValidationError, match="AUTHOR"):
        with transaction.atomic():
            film.authors.add(user_without_role)

    assert not film.authors.exists()


@pytest.mark.django_db
def test_linked_author_cannot_be_deleted_through_user_queryset(film, author):
    with pytest.raises(ProtectedError):
        with transaction.atomic():
            User.objects.filter(pk=author.pk).delete()

    assert User.objects.filter(pk=author.pk).exists()

    film.authors.clear()
    User.objects.filter(pk=author.pk).delete()
    assert not User.objects.filter(pk=author.pk).exists()


@pytest.mark.django_db
def test_local_ratings_remain_separate_from_tmdb_score(film, spectator):
    second_spectator = User.objects.create_user(username="second_spectator")
    second_spectator.groups.add(Group.objects.get(name=SPECTATOR_GROUP))
    film.tmdb_vote_average = Decimal("8.20")
    film.tmdb_vote_count = 240
    film.save()
    FilmRating.objects.create(film=film, spectator=spectator, score=2)
    FilmRating.objects.create(film=film, spectator=second_spectator, score=5)

    local_average = film.ratings.aggregate(value=Avg("score"))["value"]

    assert local_average == 3.5
    assert film.tmdb_vote_average == Decimal("8.20")
    assert film.tmdb_vote_count == 240


@pytest.mark.django_db
def test_deleting_film_cascades_to_ratings_and_favorites(film, spectator):
    FilmRating.objects.create(film=film, spectator=spectator, score=4)
    Favorite.objects.create(film=film, spectator=spectator)

    film.delete()

    assert not FilmRating.objects.exists()
    assert not Favorite.objects.exists()
