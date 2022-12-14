# Generated by Django 4.1.2 on 2022-10-18 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "appstats",
            "0005_event_counterinstance_version_gaugeinstance_version_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="counterinstance",
            name="date_created",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="counterinstance",
            name="date_updated",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="eventinstance",
            name="attributes",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="eventinstance",
            name="date_created",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="gaugeinstance",
            name="date_created",
            field=models.DateTimeField(),
        ),
    ]
