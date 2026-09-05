from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from cinema.models import Author, AuthorRating, Film, FilmRating, User
from cinema.roles import SPECTATOR_GROUP


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


class FilmWriteSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        required=False,
    )

    class Meta:
        model = Film
        fields = (
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
        )

    def to_representation(self, instance):
        return FilmSerializer(instance, context=self.context).data


class AuthorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "bio",
            "avatar",
            "source",
            "tmdb_id",
        )

    def to_representation(self, instance):
        return AuthorSerializer(instance, context=self.context).data


class FilmRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilmRating
        fields = ("id", "film", "score")
        read_only_fields = ("id", "film")


class AuthorRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorRating
        fields = ("id", "author", "score")
        read_only_fields = ("id", "author")


class SpectatorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password")
        read_only_fields = ("id",)

    def validate_password(self, value):
        candidate = User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        validate_password(value, candidate)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        user.groups.add(Group.objects.get(name=SPECTATOR_GROUP))
        return user
