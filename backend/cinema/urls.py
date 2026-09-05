from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from cinema.views import (
    AuthorDetailView,
    AuthorListView,
    FilmArchiveView,
    FilmDetailView,
    FilmListView,
    RegisterView,
    health,
    hello,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("hello/", hello, name="hello"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="auth-logout"),
    path("films/", FilmListView.as_view(), name="film-list"),
    path("films/<int:pk>/", FilmDetailView.as_view(), name="film-detail"),
    path(
        "films/<int:pk>/archive/",
        FilmArchiveView.as_view(),
        name="film-archive",
    ),
    path("authors/", AuthorListView.as_view(), name="author-list"),
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author-detail"),
]
