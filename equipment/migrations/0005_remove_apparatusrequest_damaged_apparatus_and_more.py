# Generated by Django 5.1.6 on 2025-02-28 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0004_apparatusrequest_course_code"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apparatusrequest",
            name="damaged_apparatus",
        ),
        migrations.AddField(
            model_name="apparatusrequest",
            name="damaged_apparatus",
            field=models.ManyToManyField(
                blank=True, related_name="damaged_requests", to="equipment.apparatus"
            ),
        ),
    ]
