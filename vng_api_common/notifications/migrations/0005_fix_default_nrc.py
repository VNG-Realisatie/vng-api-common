# Generated by Django 2.0.13 on 2019-04-17 10:17

from django.db import migrations


def fix_config(apps, _):
    NotificationsConfig = apps.get_model("notifications.NotificationsConfig")

    try:
        config = NotificationsConfig.objects.get()
    except NotificationsConfig.DoesNotExist:
        return

    if config.api_root == "https://ref.tst.vng.cloud/nc/api/v1":
        config.api_root = "https://ref.tst.vng.cloud/nrc/api/v1"
        config.save()


class Migration(migrations.Migration):
    dependencies = [("notifications", "0004_auto_20190325_1313")]

    operations = [migrations.RunPython(fix_config, migrations.RunPython.noop)]
