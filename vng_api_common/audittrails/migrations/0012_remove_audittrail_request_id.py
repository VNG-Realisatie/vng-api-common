# Generated by Django 2.2.8 on 2020-11-06 08:53

from django.db import migrations

from ._operations import RemoveField


class Migration(migrations.Migration):

    dependencies = [
        ("audittrails", "0011_auto_20190918_1335"),
    ]

    operations = [
        RemoveField(
            model_name="audittrail",
            name="request_id",
        ),
    ]