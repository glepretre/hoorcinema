from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from cinema.serializers import (
    CinemaTokenObtainPairSerializer,
    CinemaTokenRefreshSerializer,
)
from cinema.views import (
    AuthorDetailView,
    AuthorListView,
    AuthorRatingView,
    FavoriteListView,
    FilmArchiveView,
    FilmDetailView,
    FilmFavoriteView,
    FilmListView,
    FilmRatingView,
    FilmUnarchiveView,
    RegisterView,
    health,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path(
        "auth/login/",
        TokenObtainPairView.as_view(serializer_class=CinemaTokenObtainPairSerializer),
        name="auth-login",
    ),
    path(
        "auth/refresh/",
        TokenRefreshView.as_view(serializer_class=CinemaTokenRefreshSerializer),
        name="auth-refresh",
    ),
    path("auth/logout/", TokenBlacklistView.as_view(), name="auth-logout"),
    path("films/", FilmListView.as_view(), name="film-list"),
    path("films/<int:pk>/", FilmDetailView.as_view(), name="film-detail"),
    path(
        "films/<int:pk>/rating/",
        FilmRatingView.as_view(),
        name="film-rating",
    ),
    path(
        "films/<int:pk>/favorite/",
        FilmFavoriteView.as_view(),
        name="film-favorite",
    ),
    path(
        "films/<int:pk>/archive/",
        FilmArchiveView.as_view(),
        name="film-archive",
    ),
    path(
        "films/<int:pk>/unarchive/",
        FilmUnarchiveView.as_view(),
        name="film-unarchive",
    ),
    path("authors/", AuthorListView.as_view(), name="author-list"),
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author-detail"),
    path(
        "authors/<int:pk>/rating/",
        AuthorRatingView.as_view(),
        name="author-rating",
    ),
    path("me/favorites/", FavoriteListView.as_view(), name="favorite-list"),
]
