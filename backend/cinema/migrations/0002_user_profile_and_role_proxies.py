from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cinema", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="source",
            field=models.CharField(
                choices=[("ADMIN", "Administration"), ("TMDB", "TMDb")],
                db_index=True,
                default="ADMIN",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="tmdb_id",
            field=models.PositiveBigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.CreateModel(
            name="Author",
            fields=[],
            options={
                "ordering": ("last_name", "first_name", "username"),
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("cinema.user",),
        ),
        migrations.CreateModel(
            name="Spectator",
            fields=[],
            options={
                "ordering": ("last_name", "first_name", "username"),
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("cinema.user",),
        ),
    ]
