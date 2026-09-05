from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_role_groups(**kwargs):
    from cinema.roles import ensure_role_groups

    ensure_role_groups()


class CinemaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cinema"

    def ready(self):
        post_migrate.connect(
            create_role_groups,
            sender=self,
            dispatch_uid="cinema.create_role_groups",
        )
