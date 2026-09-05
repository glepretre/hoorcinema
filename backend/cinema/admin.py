from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Avg, Count, Prefetch

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

PROFILE_FIELDS = ("date_of_birth", "bio", "avatar", "source", "tmdb_id")
PRIVILEGE_FIELDS = ("is_staff", "is_superuser", "groups", "user_permissions")


class CinemaUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Cinema profile", {"fields": PROFILE_FIELDS}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Cinema profile", {"fields": PROFILE_FIELDS}),
    )
    list_display = UserAdmin.list_display + ("source",)
    list_filter = UserAdmin.list_filter + ("source",)


class RoleUserAdmin(CinemaUserAdmin):
    role_group_name = None

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser:
            return readonly_fields
        return (*readonly_fields, *PRIVILEGE_FIELDS)

    def save_related(self, request, form, formsets, change):
        form.save_m2m()
        form.instance.groups.add(Group.objects.get(name=self.role_group_name))
        for formset in formsets:
            self.save_formset(request, form, formset, change=change)


class HasFilmsFilter(admin.SimpleListFilter):
    title = "has films"
    parameter_name = "has_films"

    def lookups(self, request, model_admin):
        return (("yes", "Yes"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(authored_films__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(authored_films__isnull=True)
        return queryset


class LocalRatingFilter(admin.SimpleListFilter):
    title = "local rating"
    parameter_name = "local_rating"

    def lookups(self, request, model_admin):
        return (
            ("unrated", "Unrated"),
            ("1", "1 to less than 2"),
            ("2", "2 to less than 3"),
            ("3", "3 to less than 4"),
            ("4", "4 to less than 5"),
            ("5", "5"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "unrated":
            return queryset.filter(local_rating__isnull=True)
        if value in {"1", "2", "3", "4"}:
            score = int(value)
            return queryset.filter(local_rating__gte=score, local_rating__lt=score + 1)
        if value == "5":
            return queryset.filter(local_rating=5)
        return queryset


class FilmAuthorshipInline(admin.TabularInline):
    model = FilmAuthorship
    autocomplete_fields = ("film", "author")
    extra = 0
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("film", "author")


class FilmRatingInline(admin.TabularInline):
    model = FilmRating
    autocomplete_fields = ("spectator",)
    extra = 0
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("spectator")


class FavoriteInline(admin.TabularInline):
    model = Favorite
    autocomplete_fields = ("film",)
    extra = 0
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("film")


@admin.register(Author)
class AuthorAdmin(RoleUserAdmin):
    role_group_name = AUTHOR_GROUP
    inlines = (FilmAuthorshipInline,)
    list_display = CinemaUserAdmin.list_display + ("film_count",)
    list_filter = CinemaUserAdmin.list_filter + (HasFilmsFilter,)
    search_fields = CinemaUserAdmin.search_fields + ("authored_films__title",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(_film_count=Count("authored_films", distinct=True))
            .prefetch_related("authored_films")
        )

    @admin.display(description="Films", ordering="_film_count")
    def film_count(self, obj):
        return obj._film_count

    def has_delete_permission(self, request, obj=None):
        allowed = super().has_delete_permission(request, obj)
        return allowed and (obj is None or not obj.authored_films.exists())


@admin.register(Spectator)
class SpectatorAdmin(RoleUserAdmin):
    role_group_name = SPECTATOR_GROUP
    inlines = (FavoriteInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("favorites__film")


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "release_date",
        "authors_list",
        "local_rating_display",
        "source",
        "created_at",
    )
    list_filter = ("created_at", LocalRatingFilter, "status", "source")
    search_fields = (
        "title",
        "description",
        "authors__username",
        "authors__first_name",
        "authors__last_name",
    )
    date_hierarchy = "created_at"
    inlines = (FilmAuthorshipInline, FilmRatingInline)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(local_rating=Avg("ratings__score"))
            .prefetch_related(
                "authors",
                Prefetch(
                    "ratings",
                    queryset=FilmRating.objects.select_related("spectator"),
                ),
            )
        )

    @admin.display(description="Authors")
    def authors_list(self, obj):
        return ", ".join(
            author.get_full_name() or author.username for author in obj.authors.all()
        )

    @admin.display(description="Local rating", ordering="local_rating")
    def local_rating_display(self, obj):
        if obj.local_rating is None:
            return "-"
        return f"{obj.local_rating:.1f}"


@admin.register(FilmAuthorship)
class FilmAuthorshipAdmin(admin.ModelAdmin):
    list_display = ("film", "author")
    autocomplete_fields = ("film", "author")
    search_fields = ("film__title", "author__username", "author__last_name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("film", "author")


@admin.register(FilmRating)
class FilmRatingAdmin(admin.ModelAdmin):
    list_display = ("film", "spectator", "score", "updated_at")
    list_filter = ("score", "updated_at")
    autocomplete_fields = ("film", "spectator")
    search_fields = ("film__title", "spectator__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("film", "spectator")


@admin.register(AuthorRating)
class AuthorRatingAdmin(admin.ModelAdmin):
    list_display = ("author", "spectator", "score", "updated_at")
    list_filter = ("score", "updated_at")
    autocomplete_fields = ("author", "spectator")
    search_fields = ("author__username", "author__last_name", "spectator__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "spectator")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("film", "spectator", "created_at")
    list_filter = ("created_at",)
    autocomplete_fields = ("film", "spectator")
    search_fields = ("film__title", "spectator__username")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("film", "spectator")


admin.site.register(User, CinemaUserAdmin)
