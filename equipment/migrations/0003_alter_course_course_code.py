# Generated by Django 5.1.6 on 2025-03-11 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0002_alter_apparatusrequest_student"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="course_code",
            field=models.CharField(max_length=10),
        ),
    ]
