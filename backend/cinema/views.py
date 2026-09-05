from django.db.models import Avg, Prefetch
from rest_framework import filters, generics
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cinema.filters import ExactChoiceFilterBackend, NullsLastOrderingFilter
from cinema.models import Author, Film, User
from cinema.serializers import AuthorSerializer, FilmSerializer


class CinemaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class FilmQuerysetMixin:
    serializer_class = FilmSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        authors = User.objects.annotate(
            local_rating=Avg("author_ratings_received__score")
        ).order_by("last_name", "first_name", "username")
        return Film.objects.annotate(
            local_rating=Avg("ratings__score")
        ).prefetch_related(Prefetch("authors", queryset=authors))


class FilmListView(FilmQuerysetMixin, generics.ListAPIView):
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


class FilmDetailView(FilmQuerysetMixin, generics.RetrieveAPIView):
    pass


class AuthorQuerysetMixin:
    serializer_class = AuthorSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        films = Film.objects.annotate(local_rating=Avg("ratings__score")).order_by(
            "title", "pk"
        )
        return Author.objects.annotate(
            local_rating=Avg("author_ratings_received__score")
        ).prefetch_related(Prefetch("authored_films", queryset=films))


class AuthorListView(AuthorQuerysetMixin, generics.ListAPIView):
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


class AuthorDetailView(AuthorQuerysetMixin, generics.RetrieveAPIView):
    pass


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def hello(request):
    return Response({"message": "Hello, World!"})
