# Generated by Django 4.1.2 on 2022-10-19 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("appstats", "0009_alter_app_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="installedversion",
            name="latest",
            field=models.BooleanField(default=True),
        ),
    ]
