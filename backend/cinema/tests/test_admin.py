from urllib.parse import urlencode

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse

from cinema.admin import (
    AuthorAdmin,
    FavoriteAdmin,
    FavoriteInline,
    FilmAdmin,
    FilmAuthorshipAdmin,
    FilmAuthorshipInline,
    FilmRatingAdmin,
    FilmRatingInline,
    HasFilmsFilter,
    LocalRatingFilter,
    SpectatorAdmin,
)
from cinema.models import (
    Author,
    AuthorRating,
    Favorite,
    Film,
    FilmAuthorship,
    FilmRating,
    Spectator,
    User,
)
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


@pytest.fixture
def admin_request(db):
    request = RequestFactory().get("/admin/")
    request.user = User.objects.create_superuser(
        username="admin_test_user",
        password="secure-test-password",
    )
    return request


@pytest.fixture
def author(db):
    user = User.objects.create_user(username="admin_author", first_name="Ada")
    user.groups.add(Group.objects.get(name=AUTHOR_GROUP))
    return user


@pytest.fixture
def spectator(db):
    user = User.objects.create_user(username="admin_spectator")
    user.groups.add(Group.objects.get(name=SPECTATOR_GROUP))
    return user


@pytest.fixture
def rated_film(db, author, spectator):
    film = Film.objects.create(title="Rated Feature", status=Film.Status.PUBLISHED)
    film.authors.add(author)
    FilmRating.objects.create(film=film, spectator=spectator, score=4)
    return film


def test_business_models_and_expected_inlines_are_registered():
    assert isinstance(admin.site._registry[Film], FilmAdmin)
    assert isinstance(admin.site._registry[FilmAuthorship], FilmAuthorshipAdmin)
    assert isinstance(admin.site._registry[FilmRating], FilmRatingAdmin)
    assert AuthorRating in admin.site._registry
    assert isinstance(admin.site._registry[Favorite], FavoriteAdmin)
    assert admin.site._registry[Author].inlines == (FilmAuthorshipInline,)
    assert admin.site._registry[Film].inlines == (
        FilmAuthorshipInline,
        FilmRatingInline,
    )
    assert admin.site._registry[Spectator].inlines == (FavoriteInline,)


@pytest.mark.django_db
def test_film_admin_queryset_annotates_rating_and_prefetches_relations(
    admin_request, django_assert_num_queries, rated_film
):
    film_admin = admin.site._registry[Film]

    with django_assert_num_queries(3):
        film = film_admin.get_queryset(admin_request).get(pk=rated_film.pk)
        assert film_admin.authors_list(film) == "Ada"
        assert film_admin.local_rating_display(film) == "4.0"
        assert list(film.ratings.all())[0].spectator.username == "admin_spectator"


@pytest.mark.django_db
def test_local_rating_filter_includes_matching_and_unrated_films(
    admin_request, rated_film
):
    unrated_film = Film.objects.create(title="Unrated Feature")
    film_admin = admin.site._registry[Film]
    queryset = film_admin.get_queryset(admin_request)

    rated_filter = LocalRatingFilter(
        admin_request,
        {"local_rating": ["4"]},
        Film,
        film_admin,
    )
    unrated_filter = LocalRatingFilter(
        admin_request,
        {"local_rating": ["unrated"]},
        Film,
        film_admin,
    )

    assert list(rated_filter.queryset(admin_request, queryset)) == [rated_film]
    assert list(unrated_filter.queryset(admin_request, queryset)) == [unrated_film]


@pytest.mark.django_db
def test_author_filter_and_deletion_protection(admin_request, author, rated_film):
    author_without_film = User.objects.create_user(username="author_without_film")
    author_without_film.groups.add(Group.objects.get(name=AUTHOR_GROUP))
    author_admin = admin.site._registry[Author]
    queryset = author_admin.get_queryset(admin_request)

    with_films_filter = HasFilmsFilter(
        admin_request,
        {"has_films": ["yes"]},
        Author,
        author_admin,
    )
    without_films_filter = HasFilmsFilter(
        admin_request,
        {"has_films": ["no"]},
        Author,
        author_admin,
    )

    assert list(with_films_filter.queryset(admin_request, queryset)) == [author]
    assert list(without_films_filter.queryset(admin_request, queryset)) == [
        author_without_film
    ]
    assert not author_admin.has_delete_permission(admin_request, author)
    assert author_admin.has_delete_permission(admin_request, author_without_film)


@pytest.mark.django_db
def test_admin_changelists_apply_status_and_author_filters(
    client, admin_request, author, rated_film
):
    client.force_login(admin_request.user)

    film_response = client.get(
        f"{reverse('admin:cinema_film_changelist')}?"
        f"{urlencode({'status__exact': Film.Status.PUBLISHED})}"
    )
    author_response = client.get(
        f"{reverse('admin:cinema_author_changelist')}?has_films=yes"
    )

    assert film_response.status_code == 200
    assert list(film_response.context["cl"].queryset) == [rated_film]
    assert author_response.status_code == 200
    assert list(author_response.context["cl"].queryset) == [author]


@pytest.mark.django_db
def test_specialized_change_pages_render_related_objects(
    client, admin_request, author, spectator, rated_film
):
    Favorite.objects.create(film=rated_film, spectator=spectator)
    client.force_login(admin_request.user)

    author_response = client.get(
        reverse("admin:cinema_author_change", args=(author.pk,))
    )
    film_response = client.get(
        reverse("admin:cinema_film_change", args=(rated_film.pk,))
    )
    spectator_response = client.get(
        reverse("admin:cinema_spectator_change", args=(spectator.pk,))
    )

    assert author_response.status_code == 200
    assert "Rated Feature" in author_response.content.decode()
    assert film_response.status_code == 200
    assert "admin_author" in film_response.content.decode()
    assert "admin_spectator" in film_response.content.decode()
    assert spectator_response.status_code == 200
    assert "Rated Feature" in spectator_response.content.decode()


def test_admin_classes_expose_search_filters_and_optimized_querysets():
    assert "created_at" in FilmAdmin.list_filter
    assert LocalRatingFilter in FilmAdmin.list_filter
    assert "status" in FilmAdmin.list_filter
    assert HasFilmsFilter in AuthorAdmin.list_filter
    assert FilmAdmin.search_fields
    assert AuthorAdmin.search_fields
    assert SpectatorAdmin.search_fields
