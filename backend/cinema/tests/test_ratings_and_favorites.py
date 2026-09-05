import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient

from cinema.models import AuthorRating, Favorite, Film, FilmRating, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


@pytest.fixture
def interactions(db):
    author_group = Group.objects.get(name=AUTHOR_GROUP)
    spectator_group = Group.objects.get(name=SPECTATOR_GROUP)

    author = User.objects.create_user(username="rated_author")
    author.groups.add(author_group)
    spectator = User.objects.create_user(username="current_spectator")
    other_spectator = User.objects.create_user(username="other_spectator")
    spectator.groups.add(spectator_group)
    other_spectator.groups.add(spectator_group)

    film = Film.objects.create(title="Current Favorite")
    other_film = Film.objects.create(title="Someone Else's Favorite")
    film.authors.add(author)
    return {
        "author": author,
        "spectator": spectator,
        "other_spectator": other_spectator,
        "film": film,
        "other_film": other_film,
    }


def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_film_rating_is_created_then_updated_without_a_duplicate(interactions):
    client = authenticated_client(interactions["spectator"])
    url = reverse("film-rating", args=(interactions["film"].pk,))

    created = client.put(url, {"score": 2}, format="json")
    updated = client.put(url, {"score": 5}, format="json")

    assert created.status_code == 201
    assert created.json()["film"] == interactions["film"].pk
    assert updated.status_code == 200
    assert updated.json()["score"] == 5
    ratings = FilmRating.objects.filter(
        spectator=interactions["spectator"], film=interactions["film"]
    )
    assert ratings.count() == 1
    assert ratings.get().score == 5


@pytest.mark.django_db
def test_author_rating_is_created_then_updated_without_a_duplicate(interactions):
    client = authenticated_client(interactions["spectator"])
    url = reverse("author-rating", args=(interactions["author"].pk,))

    created = client.put(url, {"score": 3}, format="json")
    updated = client.put(url, {"score": 4}, format="json")

    assert created.status_code == 201
    assert created.json()["author"] == interactions["author"].pk
    assert updated.status_code == 200
    assert updated.json()["score"] == 4
    ratings = AuthorRating.objects.filter(
        spectator=interactions["spectator"], author=interactions["author"]
    )
    assert ratings.count() == 1
    assert ratings.get().score == 4


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["film-rating", "author-rating"])
@pytest.mark.parametrize("score", [0, 6, "invalid"])
def test_ratings_reject_invalid_scores(interactions, url_name, score):
    target = (
        interactions["film"] if url_name == "film-rating" else interactions["author"]
    )
    response = authenticated_client(interactions["spectator"]).put(
        reverse(url_name, args=(target.pk,)),
        {"score": score},
        format="json",
    )

    assert response.status_code == 400
    assert set(response.json()) == {"score"}


@pytest.mark.django_db
def test_rating_updates_are_reflected_in_public_aggregates(interactions):
    film_url = reverse("film-rating", args=(interactions["film"].pk,))
    author_url = reverse("author-rating", args=(interactions["author"].pk,))
    first_client = authenticated_client(interactions["spectator"])
    second_client = authenticated_client(interactions["other_spectator"])

    first_client.put(film_url, {"score": 2}, format="json")
    second_client.put(film_url, {"score": 4}, format="json")
    first_client.put(author_url, {"score": 3}, format="json")
    second_client.put(author_url, {"score": 5}, format="json")

    film = APIClient().get(reverse("film-detail", args=(interactions["film"].pk,)))
    author = APIClient().get(
        reverse("author-detail", args=(interactions["author"].pk,))
    )
    assert film.json()["local_rating"] == "3.00"
    assert author.json()["local_rating"] == "4.00"


@pytest.mark.django_db
def test_adding_and_removing_a_favorite_are_idempotent(interactions):
    client = authenticated_client(interactions["spectator"])
    url = reverse("film-favorite", args=(interactions["film"].pk,))

    created = client.post(url, {}, format="json")
    repeated = client.post(url, {}, format="json")

    assert created.status_code == 201
    assert repeated.status_code == 200
    assert (
        Favorite.objects.filter(
            spectator=interactions["spectator"], film=interactions["film"]
        ).count()
        == 1
    )

    removed = client.delete(url)
    removed_again = client.delete(url)
    assert removed.status_code == 204
    assert removed_again.status_code == 204
    assert not Favorite.objects.filter(
        spectator=interactions["spectator"], film=interactions["film"]
    ).exists()


@pytest.mark.django_db
def test_favorite_list_is_paginated_and_isolated_by_spectator(interactions):
    Favorite.objects.create(
        spectator=interactions["spectator"], film=interactions["film"]
    )
    Favorite.objects.create(
        spectator=interactions["other_spectator"], film=interactions["other_film"]
    )

    response = authenticated_client(interactions["spectator"]).get(
        reverse("favorite-list")
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert [film["title"] for film in response.json()["results"]] == [
        "Current Favorite"
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "url_name", "target_key", "payload"),
    [
        ("put", "film-rating", "film", {"score": 4}),
        ("put", "author-rating", "author", {"score": 4}),
        ("post", "film-favorite", "film", {}),
        ("delete", "film-favorite", "film", None),
        ("get", "favorite-list", None, None),
    ],
)
@pytest.mark.parametrize("actor", ["anonymous", "author"])
def test_interactions_require_the_spectator_role(
    interactions, method, url_name, target_key, payload, actor
):
    client = APIClient()
    if actor == "author":
        client.force_authenticate(interactions["author"])
    args = (interactions[target_key].pk,) if target_key else None

    response = getattr(client, method)(
        reverse(url_name, args=args),
        payload,
        format="json",
    )

    assert response.status_code == (401 if actor == "anonymous" else 403)


@pytest.mark.django_db
def test_a_user_with_author_and_spectator_roles_can_interact(interactions):
    interactions["author"].groups.add(Group.objects.get(name=SPECTATOR_GROUP))
    client = authenticated_client(interactions["author"])

    response = client.put(
        reverse("film-rating", args=(interactions["film"].pk,)),
        {"score": 5},
        format="json",
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_author_rating_rejects_a_user_without_the_author_role(interactions):
    response = authenticated_client(interactions["spectator"]).put(
        reverse("author-rating", args=(interactions["other_spectator"].pk,)),
        {"score": 5},
        format="json",
    )

    assert response.status_code == 404
