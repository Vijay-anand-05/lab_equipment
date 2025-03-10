# Generated by Django 5.1.6 on 2025-03-01 07:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0009_apparatus_fine_amount"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apparatusrequest",
            name="fine_amount",
        ),
        migrations.CreateModel(
            name="ApparatusRequestDamage",
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
                (
                    "fine_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("remarks", models.TextField(blank=True, null=True)),
                (
                    "apparatus",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="equipment.apparatus",
                    ),
                ),
                (
                    "apparatus_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="equipment.apparatusrequest",
                    ),
                ),
            ],
            options={
                "db_table": "apparatus_request_damage",
            },
        ),
        migrations.AlterField(
            model_name="apparatusrequest",
            name="damaged_apparatus",
            field=models.ManyToManyField(
                blank=True,
                related_name="damaged_requests",
                through="equipment.ApparatusRequestDamage",
                to="equipment.apparatus",
            ),
        ),
    ]
