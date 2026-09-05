import pytest
from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory

from cinema.admin import AuthorAdmin, CinemaUserAdmin, SpectatorAdmin
from cinema.models import Author, Spectator, User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP


@pytest.mark.django_db
def test_role_groups_have_proxy_permissions():
    author_permissions = set(
        Group.objects.get(name=AUTHOR_GROUP).permissions.values_list(
            "codename", flat=True
        )
    )
    spectator_permissions = set(
        Group.objects.get(name=SPECTATOR_GROUP).permissions.values_list(
            "codename", flat=True
        )
    )

    assert author_permissions == {"view_author"}
    assert spectator_permissions == {"view_spectator"}


@pytest.mark.django_db
def test_roles_are_cumulative_and_proxy_managers_filter_users():
    author_group = Group.objects.get(name=AUTHOR_GROUP)
    spectator_group = Group.objects.get(name=SPECTATOR_GROUP)
    both_roles = User.objects.create_user(username="both_roles")
    author_only = User.objects.create_user(username="author_only")
    no_role = User.objects.create_user(username="no_role")

    both_roles.groups.add(author_group, spectator_group)
    author_only.groups.add(author_group)

    assert set(Author.objects.values_list("username", flat=True)) == {
        "author_only",
        "both_roles",
    }
    assert list(Spectator.objects.values_list("username", flat=True)) == ["both_roles"]
    assert isinstance(Author.objects.get(pk=both_roles.pk), Author)
    assert isinstance(Spectator.objects.get(pk=both_roles.pk), Spectator)
    assert no_role not in Author.objects.all()
    assert no_role not in Spectator.objects.all()


def test_specialized_user_models_are_registered_in_admin():
    assert isinstance(admin.site._registry[User], CinemaUserAdmin)
    assert isinstance(admin.site._registry[Author], AuthorAdmin)
    assert isinstance(admin.site._registry[Spectator], SpectatorAdmin)


@pytest.mark.django_db
def test_role_admin_protects_privileges_and_preserves_role_group(monkeypatch):
    staff_user = User.objects.create_user(username="staff", is_staff=True)
    author = User.objects.create_user(username="admin_created_author")
    request = RequestFactory().get("/admin/")
    request.user = staff_user
    author_admin = admin.site._registry[Author]

    class Form:
        instance = author

        @staticmethod
        def save_m2m():
            pass

    def save_formset(request, form, formset, change):
        assert author.groups.filter(name=AUTHOR_GROUP).exists()

    monkeypatch.setattr(author_admin, "save_formset", save_formset)

    assert {
        "is_staff",
        "is_superuser",
        "groups",
        "user_permissions",
    }.issubset(author_admin.get_readonly_fields(request, author))

    author_admin.save_related(request, Form(), [object()], change=False)

    assert author.groups.get().name == AUTHOR_GROUP
    assert Author.objects.filter(pk=author.pk).exists()
