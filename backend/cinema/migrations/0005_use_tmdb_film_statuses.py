from django.db import migrations, models

FORWARD_STATUSES = {
    "DRAFT": "Planned",
    "PUBLISHED": "Released",
}
REVERSE_STATUSES = {
    "Rumored": "DRAFT",
    "Planned": "DRAFT",
    "In Production": "DRAFT",
    "Post Production": "DRAFT",
    "Released": "PUBLISHED",
    "Canceled": "ARCHIVED",
}


def migrate_statuses(apps, schema_editor):
    film = apps.get_model("cinema", "Film")
    for old_status, new_status in FORWARD_STATUSES.items():
        film.objects.filter(status=old_status).update(status=new_status)
    film.objects.filter(status="ARCHIVED").update(
        is_archived=True,
        status="Released",
    )


def restore_statuses(apps, schema_editor):
    film = apps.get_model("cinema", "Film")
    for new_status, old_status in REVERSE_STATUSES.items():
        film.objects.filter(status=new_status).update(status=old_status)
    film.objects.filter(is_archived=True).update(status="ARCHIVED")


class Migration(migrations.Migration):
    dependencies = [("cinema", "0004_alter_user_managers_user_unique_user_username_ci")]

    operations = [
        migrations.RemoveConstraint(
            model_name="film",
            name="film_valid_status",
        ),
        migrations.AlterField(
            model_name="film",
            name="status",
            field=models.CharField(
                choices=[
                    ("Rumored", "Rumored"),
                    ("Planned", "Planned"),
                    ("In Production", "In Production"),
                    ("Post Production", "Post Production"),
                    ("Released", "Released"),
                    ("Canceled", "Canceled"),
                ],
                db_index=True,
                default="Planned",
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="film",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.RunPython(migrate_statuses, restore_statuses),
        migrations.AddConstraint(
            model_name="film",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=(
                        "Rumored",
                        "Planned",
                        "In Production",
                        "Post Production",
                        "Released",
                        "Canceled",
                    )
                ),
                name="film_valid_status",
            ),
        ),
    ]
