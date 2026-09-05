from datetime import date

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APIClient

from cinema.models import AuthorRating, Film, FilmRating, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP
from cinema.serializers import AuthorSerializer, FilmSerializer


@pytest.fixture
def catalogue(db):
    author_group = Group.objects.get(name=AUTHOR_GROUP)
    spectator_group = Group.objects.get(name=SPECTATOR_GROUP)
    local_author = User.objects.create_user(
        username="ada_director",
        first_name="Ada",
        last_name="Director",
        email="ada@example.com",
    )
    remote_author = User.objects.create_user(
        username="tmdb_84",
        first_name="Grace",
        last_name="Writer",
        source=User.Source.TMDB,
        tmdb_id=84,
    )
    local_author.groups.add(author_group)
    remote_author.groups.add(author_group)

    first_spectator = User.objects.create_user(username="first_reviewer")
    second_spectator = User.objects.create_user(username="second_reviewer")
    first_spectator.groups.add(spectator_group)
    second_spectator.groups.add(spectator_group)

    local_film = Film.objects.create(
        title="Aurora Story",
        description="A northern drama.",
        release_date=date(2020, 1, 2),
        status=Film.Status.PUBLISHED,
    )
    remote_film = Film.objects.create(
        title="Zenith Journey",
        release_date=date(2022, 5, 6),
        status=Film.Status.DRAFT,
        source=Film.Source.TMDB,
        tmdb_id=42,
        tmdb_vote_average="8.25",
        tmdb_vote_count=200,
    )
    unrated_film = Film.objects.create(
        title="Middle Archive",
        release_date=date(2019, 3, 4),
        status=Film.Status.ARCHIVED,
    )
    local_film.authors.add(local_author)
    remote_film.authors.add(remote_author)
    FilmRating.objects.create(
        film=local_film,
        spectator=first_spectator,
        score=2,
    )
    FilmRating.objects.create(
        film=local_film,
        spectator=second_spectator,
        score=4,
    )
    FilmRating.objects.create(
        film=remote_film,
        spectator=first_spectator,
        score=5,
    )
    AuthorRating.objects.create(
        author=local_author,
        spectator=first_spectator,
        score=3,
    )
    AuthorRating.objects.create(
        author=local_author,
        spectator=second_spectator,
        score=5,
    )
    return {
        "local_author": local_author,
        "remote_author": remote_author,
        "local_film": local_film,
        "remote_film": remote_film,
        "unrated_film": unrated_film,
    }


@pytest.mark.django_db
def test_anonymous_film_list_is_paginated_and_nested(catalogue):
    response = APIClient().get(reverse("film-list"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert set(response.json()) == {"count", "next", "previous", "results"}
    assert response.json()["count"] == 3
    film = response.json()["results"][0]
    assert film["title"] == "Aurora Story"
    assert film["local_rating"] == "3.00"
    assert film["authors"] == [
        {
            "id": catalogue["local_author"].pk,
            "username": "ada_director",
            "first_name": "Ada",
            "last_name": "Director",
            "avatar": "",
            "source": "ADMIN",
            "tmdb_id": None,
            "local_rating": "4.00",
        }
    ]


@pytest.mark.django_db
def test_anonymous_film_detail_exposes_external_and_related_data(catalogue):
    response = APIClient().get(
        reverse("film-detail", args=(catalogue["remote_film"].pk,))
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Zenith Journey"
    assert response.json()["tmdb_vote_average"] == "8.25"
    assert response.json()["tmdb_vote_count"] == 200
    assert response.json()["local_rating"] == "5.00"
    assert response.json()["authors"][0]["username"] == "tmdb_84"


@pytest.mark.django_db
def test_anonymous_author_endpoints_include_nested_films(catalogue):
    list_response = APIClient().get(reverse("author-list"))
    detail_response = APIClient().get(
        reverse("author-detail", args=(catalogue["local_author"].pk,))
    )

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 2
    assert detail_response.status_code == 200
    assert detail_response.json()["email"] == "ada@example.com"
    assert detail_response.json()["local_rating"] == "4.00"
    assert detail_response.json()["films"] == [
        {
            "id": catalogue["local_film"].pk,
            "title": "Aurora Story",
            "release_date": "2020-01-02",
            "status": "PUBLISHED",
            "source": "ADMIN",
            "poster_path": "",
            "local_rating": "3.00",
        }
    ]


@pytest.mark.django_db
def test_film_filters_search_and_ordering(catalogue):
    client = APIClient()

    filtered = client.get(
        reverse("film-list"),
        {"status": "PUBLISHED", "source": "ADMIN", "search": "aurora"},
    )
    by_release_date = client.get(reverse("film-list"), {"ordering": "-release_date"})
    by_rating = client.get(reverse("film-list"), {"ordering": "-local_rating"})

    assert [film["title"] for film in filtered.json()["results"]] == ["Aurora Story"]
    assert [film["title"] for film in by_release_date.json()["results"]] == [
        "Zenith Journey",
        "Aurora Story",
        "Middle Archive",
    ]
    assert [film["title"] for film in by_rating.json()["results"]] == [
        "Zenith Journey",
        "Aurora Story",
        "Middle Archive",
    ]


@pytest.mark.django_db
def test_author_source_search_and_ordering(catalogue):
    response = APIClient().get(
        reverse("author-list"),
        {"source": "TMDB", "search": "grace", "ordering": "last_name"},
    )

    assert [author["username"] for author in response.json()["results"]] == ["tmdb_84"]


@pytest.mark.django_db
def test_list_pagination_supports_page_and_bounded_page_size(catalogue):
    response = APIClient().get(reverse("film-list"), {"page": 2, "page_size": 2})

    assert response.status_code == 200
    assert response.json()["count"] == 3
    assert response.json()["previous"] is not None
    assert len(response.json()["results"]) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "parameters", "field"),
    [
        ("film-list", {"status": "INVALID"}, "status"),
        ("film-list", {"source": "INVALID"}, "source"),
        ("author-list", {"source": "INVALID"}, "source"),
    ],
)
def test_invalid_choice_filters_return_json_400(url_name, parameters, field):
    response = APIClient().get(reverse(url_name), parameters)

    assert response.status_code == 400
    assert field in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "url_name", "detail"),
    [
        ("post", "film-list", False),
        ("patch", "film-detail", True),
        ("delete", "film-detail", True),
        ("post", "author-list", False),
        ("patch", "author-detail", True),
        ("delete", "author-detail", True),
    ],
)
def test_public_endpoints_are_read_only(method, url_name, detail, catalogue):
    args = (
        (catalogue["local_film"].pk,)
        if "film" in url_name
        else (catalogue["local_author"].pk,)
    )
    url = reverse(url_name, args=args if detail else None)

    response = getattr(APIClient(), method)(url, {}, format="json")

    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["film-list", "author-list"])
def test_list_query_count_is_constant(url_name, catalogue, django_assert_num_queries):
    with django_assert_num_queries(3):
        response = APIClient().get(reverse(url_name))
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0


def test_public_serializers_do_not_use_serializer_method_fields():
    for serializer_class in (FilmSerializer, AuthorSerializer):
        assert not any(
            isinstance(field, serializers.SerializerMethodField)
            for field in serializer_class().fields.values()
        )
