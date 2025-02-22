# Generated by Django 5.1.6 on 2025-02-17 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "dept_code",
                    models.CharField(max_length=200, primary_key=True, serialize=False),
                ),
                ("department", models.CharField(max_length=500)),
            ],
            options={
                "db_table": "application_departments",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "student_regno",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("student_dob", models.DateField(blank=True, null=True)),
                (
                    "student_password",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
            ],
            options={
                "db_table": "core_student",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Student_cgpa",
            fields=[
                (
                    "reg_no",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("batch", models.CharField(max_length=100)),
                ("student_name", models.CharField(max_length=100)),
                ("department", models.CharField(max_length=100)),
                ("cgpa", models.FloatField()),
                ("sslc", models.FloatField()),
                ("hsc", models.CharField(blank=True, max_length=20, null=True)),
                ("diploma", models.CharField(blank=True, max_length=20, null=True)),
                ("bag_of_log", models.IntegerField()),
                ("history_of_arrear", models.IntegerField()),
                (
                    "admission_type",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "contact_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                ("semester1", models.CharField(blank=True, max_length=20, null=True)),
                ("semester2", models.CharField(blank=True, max_length=20, null=True)),
                ("semester3", models.CharField(blank=True, max_length=20, null=True)),
                ("semester4", models.CharField(blank=True, max_length=20, null=True)),
                ("semester5", models.CharField(blank=True, max_length=20, null=True)),
                ("semester6", models.CharField(blank=True, max_length=20, null=True)),
                ("semester7", models.CharField(blank=True, max_length=20, null=True)),
                ("semester8", models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                "db_table": "application_student",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("Name", models.CharField(max_length=100)),
                ("user_name", models.CharField(max_length=100)),
                ("staff_id", models.CharField(max_length=100)),
                ("Department", models.CharField(max_length=100)),
                ("Department_code", models.CharField(max_length=100)),
                ("email", models.CharField(max_length=100)),
                ("role", models.CharField(max_length=100)),
                (
                    "default_role",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("Password", models.CharField(max_length=100)),
                ("confirm_Password", models.CharField(max_length=100)),
            ],
            options={
                "db_table": "application_user",
                "managed": False,
            },
        ),
    ]
