# Generated by Django 5.1.6 on 2025-03-09 13:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0015_apparatusrequest_remarks"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apparatusrequest",
            name="fine_amount",
        ),
        migrations.RemoveField(
            model_name="apparatusrequest",
            name="remarks",
        ),
    ]
