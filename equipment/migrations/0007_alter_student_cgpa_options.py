# Generated by Django 5.1.6 on 2025-02-17 10:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "equipment",
            "0006_alter_student_cgpa_options_alter_student_cgpa_gender_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="student_cgpa",
            options={"managed": False},
        ),
    ]
