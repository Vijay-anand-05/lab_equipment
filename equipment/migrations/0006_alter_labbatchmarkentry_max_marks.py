# Generated by Django 5.1.6 on 2025-03-21 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0005_labbatchmarkentry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="labbatchmarkentry",
            name="max_marks",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
