# Generated by Django 5.1.6 on 2025-03-07 17:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0013_regulation_master_apparatusrequest_fine_amount"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="student_cgpa",
            options={"managed": True},
        ),
    ]
