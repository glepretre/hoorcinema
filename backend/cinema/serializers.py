from rest_framework import serializers

from cinema.models import Author, Film, User


class LocalRatingField(serializers.DecimalField):
    def __init__(self, **kwargs):
        super().__init__(
            allow_null=True,
            decimal_places=2,
            max_digits=3,
            read_only=True,
            **kwargs,
        )


class AuthorSummarySerializer(serializers.ModelSerializer):
    local_rating = LocalRatingField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "source",
            "tmdb_id",
            "local_rating",
        )


class FilmSummarySerializer(serializers.ModelSerializer):
    local_rating = LocalRatingField()

    class Meta:
        model = Film
        fields = (
            "id",
            "title",
            "release_date",
            "status",
            "source",
            "poster_path",
            "local_rating",
        )


class FilmSerializer(serializers.ModelSerializer):
    authors = AuthorSummarySerializer(many=True, read_only=True)
    local_rating = LocalRatingField()

    class Meta:
        model = Film
        fields = (
            "id",
            "title",
            "description",
            "release_date",
            "status",
            "authors",
            "source",
            "tmdb_id",
            "tmdb_vote_average",
            "tmdb_vote_count",
            "poster_path",
            "local_rating",
            "created_at",
            "updated_at",
        )


class AuthorSerializer(serializers.ModelSerializer):
    films = FilmSummarySerializer(source="authored_films", many=True, read_only=True)
    local_rating = LocalRatingField()

    class Meta:
        model = Author
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "bio",
            "avatar",
            "source",
            "tmdb_id",
            "local_rating",
            "films",
        )
