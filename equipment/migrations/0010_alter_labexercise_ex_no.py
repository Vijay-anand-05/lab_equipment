# Generated by Django 5.1.6 on 2025-02-20 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0009_alter_student_cgpa_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="labexercise",
            name="Ex_no",
            field=models.CharField(max_length=50),
        ),
    ]
