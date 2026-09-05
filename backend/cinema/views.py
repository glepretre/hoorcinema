from django.db.models import Avg, Prefetch
from rest_framework import filters, generics, status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cinema.filters import ExactChoiceFilterBackend, NullsLastOrderingFilter
from cinema.models import Author, Film, User
from cinema.permissions import StaffDjangoModelPermissions
from cinema.serializers import (
    AuthorSerializer,
    AuthorWriteSerializer,
    FilmSerializer,
    FilmWriteSerializer,
    SpectatorRegistrationSerializer,
)


class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SpectatorRegistrationSerializer


class CinemaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class FilmQuerysetMixin:
    serializer_class = FilmSerializer

    def get_queryset(self):
        authors = User.objects.annotate(
            local_rating=Avg("author_ratings_received__score")
        ).order_by("last_name", "first_name", "username")
        return Film.objects.annotate(
            local_rating=Avg("ratings__score")
        ).prefetch_related(Prefetch("authors", queryset=authors))


class FilmListView(FilmQuerysetMixin, generics.ListAPIView):
    permission_classes = (AllowAny,)
    pagination_class = CinemaPagination
    filter_backends = (
        ExactChoiceFilterBackend,
        filters.SearchFilter,
        NullsLastOrderingFilter,
    )
    choice_filter_fields = ("status", "source")
    search_fields = ("title",)
    ordering_fields = ("release_date", "local_rating", "title")
    ordering = ("title", "pk")


class FilmDetailView(FilmQuerysetMixin, generics.RetrieveUpdateAPIView):
    http_method_names = ("get", "patch", "head", "options")
    permission_classes = (StaffDjangoModelPermissions,)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return FilmWriteSerializer
        return super().get_serializer_class()


class FilmArchiveView(FilmQuerysetMixin, generics.GenericAPIView):
    http_method_names = ("patch", "options")
    permission_classes = (StaffDjangoModelPermissions,)

    def patch(self, request, *args, **kwargs):
        film = self.get_object()
        if film.status != Film.Status.ARCHIVED:
            film.status = Film.Status.ARCHIVED
            film.save(update_fields=("status", "updated_at"))
        return Response(
            FilmSerializer(film, context=self.get_serializer_context()).data
        )


class AuthorQuerysetMixin:
    serializer_class = AuthorSerializer

    def get_queryset(self):
        films = Film.objects.annotate(local_rating=Avg("ratings__score")).order_by(
            "title", "pk"
        )
        return Author.objects.annotate(
            local_rating=Avg("author_ratings_received__score")
        ).prefetch_related(Prefetch("authored_films", queryset=films))


class AuthorListView(AuthorQuerysetMixin, generics.ListAPIView):
    permission_classes = (AllowAny,)
    pagination_class = CinemaPagination
    filter_backends = (
        ExactChoiceFilterBackend,
        filters.SearchFilter,
        NullsLastOrderingFilter,
    )
    choice_filter_fields = ("source",)
    search_fields = ("username", "first_name", "last_name")
    ordering_fields = ("last_name", "first_name", "username", "local_rating")
    ordering = ("last_name", "first_name", "username")


class AuthorDetailView(AuthorQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ("get", "patch", "delete", "head", "options")
    permission_classes = (StaffDjangoModelPermissions,)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AuthorWriteSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        author = self.get_object()
        if author.authored_films.exists():
            return Response(
                {
                    "code": "author_has_films",
                    "detail": "Authors with films cannot be deleted.",
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def hello(request):
    return Response({"message": "Hello, World!"})
