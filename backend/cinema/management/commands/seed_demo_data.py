import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cinema.roles import AUTHOR_GROUP, SPECTATOR_GROUP, ensure_role_groups

DEMO_USERS = (
    {
        "username": "demo_author",
        "email": "author@example.com",
        "first_name": "Demo",
        "last_name": "Author",
        "password_env": "DEMO_AUTHOR_PASSWORD",
        "group": AUTHOR_GROUP,
    },
    {
        "username": "demo_spectator",
        "email": "spectator@example.com",
        "first_name": "Demo",
        "last_name": "Spectator",
        "password_env": "DEMO_SPECTATOR_PASSWORD",
        "group": SPECTATOR_GROUP,
    },
    {
        "username": "demo_admin",
        "email": "admin@example.com",
        "first_name": "Demo",
        "last_name": "Administrator",
        "password_env": "DEMO_ADMIN_PASSWORD",
        "is_staff": True,
        "is_superuser": True,
    },
)


class Command(BaseCommand):
    help = "Create or update the demonstration users and role groups."

    def handle(self, *args, **options):
        missing_variables = [
            user["password_env"]
            for user in DEMO_USERS
            if not os.getenv(user["password_env"])
        ]
        if missing_variables:
            names = ", ".join(missing_variables)
            raise CommandError(f"Missing required environment variables: {names}")

        user_model = get_user_model()
        for user_data in DEMO_USERS:
            candidate = user_model(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
            try:
                validate_password(os.environ[user_data["password_env"]], user=candidate)
            except ValidationError as error:
                messages = " ".join(error.messages)
                raise CommandError(
                    f"Invalid password for {user_data['username']}: {messages}"
                ) from error

        with transaction.atomic():
            groups = ensure_role_groups()
            for user_data in DEMO_USERS:
                username = user_data["username"]
                defaults = {
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                    "is_staff": user_data.get("is_staff", False),
                    "is_superuser": user_data.get("is_superuser", False),
                }
                user = user_model.objects.filter(username=username).first()
                created = user is None
                if created:
                    user = user_model(username=username)
                elif user.email != user_data["email"]:
                    raise CommandError(
                        f"Refusing to overwrite existing user {username}"
                    )

                for field, value in defaults.items():
                    setattr(user, field, value)
                user.set_password(os.environ[user_data["password_env"]])
                user.save()

                group_name = user_data.get("group")
                if group_name:
                    user.groups.add(groups[group_name])

                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} {username}")

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
