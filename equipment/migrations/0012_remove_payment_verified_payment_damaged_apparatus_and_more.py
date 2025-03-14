# Generated by Django 5.1.6 on 2025-03-11 16:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0011_payment_verified"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payment",
            name="verified",
        ),
        migrations.AddField(
            model_name="payment",
            name="damaged_apparatus",
            field=models.ManyToManyField(
                blank=True,
                related_name="damage_payments",
                to="equipment.apparatusrequestdamage",
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="lab_batch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="batch_payments",
                to="equipment.labbatchassignment",
            ),
        ),
    ]
