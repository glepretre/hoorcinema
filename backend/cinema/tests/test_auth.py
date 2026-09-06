import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from cinema.models import Film, User
from cinema.roles import SPECTATOR_GROUP


@pytest.mark.django_db
def test_registration_creates_only_a_spectator_with_hashed_password():
    response = APIClient().post(
        reverse("auth-register"),
        {
            "username": "new_spectator",
            "email": "spectator@example.com",
            "first_name": "New",
            "last_name": "Spectator",
            "password": "Secure-test-password-42",
        },
        format="json",
    )

    assert response.status_code == 201
    assert "password" not in response.json()
    user = User.objects.get(username="new_spectator")
    assert user.check_password("Secure-test-password-42")
    assert list(user.groups.values_list("name", flat=True)) == [SPECTATOR_GROUP]
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_registration_validates_password_and_unique_username():
    User.objects.create_user(username="existing")
    client = APIClient()

    weak_password = client.post(
        reverse("auth-register"),
        {"username": "weak", "password": "password"},
        format="json",
    )
    duplicate = client.post(
        reverse("auth-register"),
        {"username": "EXISTING", "password": "Secure-test-password-42"},
        format="json",
    )

    assert weak_password.status_code == 400
    assert set(weak_password.json()) == {"password"}
    assert duplicate.status_code == 400
    assert set(duplicate.json()) == {"username"}


@pytest.fixture
def spectator(db):
    user = User.objects.create_user(
        username="viewer",
        password="Secure-test-password-42",
    )
    user.groups.add(Group.objects.get(name=SPECTATOR_GROUP))
    return user


def login(client, spectator):
    return client.post(
        reverse("auth-login"),
        {"username": spectator.username, "password": "Secure-test-password-42"},
        format="json",
    )


@pytest.mark.django_db
def test_login_returns_access_and_refresh_tokens(spectator):
    response = login(APIClient(), spectator)

    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}
    assert AccessToken(response.json()["access"])["can_change_film"] is False
    assert AccessToken(response.json()["access"])["can_rate"] is True


@pytest.mark.django_db
def test_login_exposes_film_change_capability_for_authorized_staff():
    staff = User.objects.create_user(
        username="film_manager",
        password="Secure-test-password-42",
        is_staff=True,
    )
    staff.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="cinema",
            codename="change_film",
        )
    )

    response = APIClient().post(
        reverse("auth-login"),
        {"username": staff.username, "password": "Secure-test-password-42"},
        format="json",
    )

    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["can_change_film"] is True
    assert AccessToken(response.json()["access"])["can_rate"] is False


@pytest.mark.django_db
def test_refresh_recomputes_film_change_capability(spectator):
    client = APIClient()
    refresh = login(client, spectator).json()["refresh"]
    spectator.is_staff = True
    spectator.save(update_fields=("is_staff",))
    spectator.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="cinema",
            codename="change_film",
        )
    )

    response = client.post(
        reverse("auth-refresh"),
        {"refresh": refresh},
        format="json",
    )

    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["can_change_film"] is True
    assert AccessToken(response.json()["access"])["can_rate"] is True


@pytest.mark.django_db
def test_refresh_rejects_a_deleted_user(spectator):
    client = APIClient()
    refresh = login(client, spectator).json()["refresh"]
    spectator.delete()

    response = client.post(
        reverse("auth-refresh"),
        {"refresh": refresh},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_login_username_is_case_insensitive(spectator):
    response = APIClient().post(
        reverse("auth-login"),
        {"username": "VIEWER", "password": "Secure-test-password-42"},
        format="json",
    )

    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(spectator):
    response = APIClient().post(
        reverse("auth-login"),
        {"username": spectator.username, "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_rotates_token_and_blacklists_previous_token(spectator):
    client = APIClient()
    previous_refresh = login(client, spectator).json()["refresh"]
    previous_jti = RefreshToken(previous_refresh)["jti"]

    response = client.post(
        reverse("auth-refresh"),
        {"refresh": previous_refresh},
        format="json",
    )

    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}
    assert response.json()["refresh"] != previous_refresh
    assert AccessToken(response.json()["access"])["can_change_film"] is False
    assert AccessToken(response.json()["access"])["can_rate"] is True
    assert BlacklistedToken.objects.filter(token__jti=previous_jti).exists()

    rejected = client.post(
        reverse("auth-refresh"),
        {"refresh": previous_refresh},
        format="json",
    )
    assert rejected.status_code == 401


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(spectator):
    client = APIClient()
    refresh = login(client, spectator).json()["refresh"]
    refresh_jti = RefreshToken(refresh)["jti"]

    response = client.post(
        reverse("auth-logout"),
        {"refresh": refresh},
        format="json",
    )

    assert response.status_code == 200
    assert BlacklistedToken.objects.filter(token__jti=refresh_jti).exists()

    repeated = client.post(
        reverse("auth-logout"),
        {"refresh": refresh},
        format="json",
    )
    assert repeated.status_code == 401


@pytest.mark.django_db
def test_bearer_access_token_authenticates_protected_calls(spectator):
    film = Film.objects.create(title="Protected Film")
    access = login(APIClient(), spectator).json()["access"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = client.patch(
        reverse("film-archive", args=(film.pk,)),
        {},
        format="json",
    )

    assert response.status_code == 403
