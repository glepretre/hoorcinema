from django.urls import path

from cinema.views import (
    AuthorDetailView,
    AuthorListView,
    FilmDetailView,
    FilmListView,
    health,
    hello,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("hello/", hello, name="hello"),
    path("films/", FilmListView.as_view(), name="film-list"),
    path("films/<int:pk>/", FilmDetailView.as_view(), name="film-detail"),
    path("authors/", AuthorListView.as_view(), name="author-list"),
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author-detail"),
]
