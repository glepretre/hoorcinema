from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from cinema.models import Author, Spectator, User
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
        super().save_related(request, form, formsets, change)
        form.instance.groups.add(Group.objects.get(name=self.role_group_name))


@admin.register(Author)
class AuthorAdmin(RoleUserAdmin):
    role_group_name = AUTHOR_GROUP


@admin.register(Spectator)
class SpectatorAdmin(RoleUserAdmin):
    role_group_name = SPECTATOR_GROUP


admin.site.register(User, CinemaUserAdmin)
