# Generated by Django 5.1.6 on 2025-03-19 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="labexercise",
            name="experiment_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
