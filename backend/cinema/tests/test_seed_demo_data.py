import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

from cinema.models import User
from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP

PASSWORDS = {
    "DEMO_AUTHOR_PASSWORD": "author-test-password",
    "DEMO_SPECTATOR_PASSWORD": "spectator-test-password",
    "DEMO_ADMIN_PASSWORD": "admin-test-password",
}


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent(monkeypatch):
    for name, password in PASSWORDS.items():
        monkeypatch.setenv(name, password)

    call_command("seed_demo_data")
    call_command("seed_demo_data")

    assert User.objects.filter(username__startswith="demo_").count() == 3

    author = User.objects.get(username="demo_author")
    spectator = User.objects.get(username="demo_spectator")
    administrator = User.objects.get(username="demo_admin")

    assert author.groups.get().name == AUTHOR_GROUP
    assert spectator.groups.get().name == SPECTATOR_GROUP
    assert author.check_password(PASSWORDS["DEMO_AUTHOR_PASSWORD"])
    assert spectator.check_password(PASSWORDS["DEMO_SPECTATOR_PASSWORD"])
    assert administrator.check_password(PASSWORDS["DEMO_ADMIN_PASSWORD"])
    assert administrator.is_staff
    assert administrator.is_superuser
    assert Group.objects.filter(name__in=[AUTHOR_GROUP, SPECTATOR_GROUP]).count() == 2


@pytest.mark.django_db
def test_seed_demo_data_requires_all_passwords(monkeypatch):
    for name in PASSWORDS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(CommandError, match="DEMO_AUTHOR_PASSWORD"):
        call_command("seed_demo_data")

    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
def test_seed_demo_data_rejects_weak_passwords(monkeypatch):
    for name in PASSWORDS:
        monkeypatch.setenv(name, "short")

    with pytest.raises(CommandError, match="Invalid password for demo_author"):
        call_command("seed_demo_data")

    assert not User.objects.filter(username__startswith="demo_").exists()


@pytest.mark.django_db
def test_seed_demo_data_refuses_username_collisions(monkeypatch):
    for name, password in PASSWORDS.items():
        monkeypatch.setenv(name, password)
    existing_user = User.objects.create_user(
        username="demo_author",
        email="real-user@example.com",
        password="original-secure-password",
    )

    with pytest.raises(CommandError, match="Refusing to overwrite"):
        call_command("seed_demo_data")

    existing_user.refresh_from_db()
    assert existing_user.email == "real-user@example.com"
    assert existing_user.check_password("original-secure-password")
    assert not User.objects.filter(username="demo_spectator").exists()
