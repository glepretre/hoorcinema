from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

AUTHOR_GROUP = "AUTHOR"
SPECTATOR_GROUP = "SPECTATOR"

ROLE_MODELS = {
    AUTHOR_GROUP: "Author",
    SPECTATOR_GROUP: "Spectator",
}


def ensure_role_groups():
    from cinema.models import Author, Spectator

    proxy_models = {"Author": Author, "Spectator": Spectator}
    groups = {}

    for group_name, model_name in ROLE_MODELS.items():
        model = proxy_models[model_name]
        content_type = ContentType.objects.get_for_model(
            model, for_concrete_model=False
        )
        permissions = Permission.objects.filter(
            codename=f"view_{model._meta.model_name}",
            content_type=content_type,
        )
        group, _ = Group.objects.get_or_create(name=group_name)
        group.permissions.set(permissions)
        groups[group_name] = group

    return groups
