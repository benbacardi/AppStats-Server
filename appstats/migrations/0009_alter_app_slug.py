# Generated by Django 4.1.2 on 2022-10-19 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("appstats", "0008_app_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="app",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]