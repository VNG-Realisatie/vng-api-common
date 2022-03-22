# Generated by Django 2.2.27 on 2022-03-18 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authorizations", "0014_auto_20201221_0905"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authorizationsconfig",
            name="component",
            field=models.CharField(
                choices=[
                    ("ac", "Autorisaties API"),
                    ("nrc", "Notificaties API"),
                    ("zrc", "Zaken API"),
                    ("ztc", "Catalogi API"),
                    ("drc", "Documenten API"),
                    ("brc", "Besluiten API"),
                    ("cmc", "Contactmomenten API"),
                    ("kc", "Klanten API"),
                    ("vrc", "Verzoeken API"),
                ],
                default="zrc",
                max_length=50,
                verbose_name="component",
            ),
        ),
        migrations.AlterField(
            model_name="autorisatie",
            name="component",
            field=models.CharField(
                choices=[
                    ("ac", "Autorisaties API"),
                    ("nrc", "Notificaties API"),
                    ("zrc", "Zaken API"),
                    ("ztc", "Catalogi API"),
                    ("drc", "Documenten API"),
                    ("brc", "Besluiten API"),
                    ("cmc", "Contactmomenten API"),
                    ("kc", "Klanten API"),
                    ("vrc", "Verzoeken API"),
                ],
                help_text="Component waarop autorisatie van toepassing is.",
                max_length=50,
                verbose_name="component",
            ),
        ),
    ]