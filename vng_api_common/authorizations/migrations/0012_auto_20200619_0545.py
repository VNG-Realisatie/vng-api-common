# Generated by Django 2.2.6 on 2020-06-19 05:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authorizations", "0011_auto_20191114_0728"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authorizationsconfig",
            name="component",
            field=models.CharField(
                choices=[
                    ("ac", "Autorisatiecomponent"),
                    ("nrc", "Notificatierouteringcomponent"),
                    ("zrc", "Zaakregistratiecomponent"),
                    ("ztc", "Zaaktypecatalogus"),
                    ("drc", "Documentregistratiecomponent"),
                    ("brc", "Besluitregistratiecomponent"),
                    ("kic", "Klantinteractiescomponent"),
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
                    ("ac", "Autorisatiecomponent"),
                    ("nrc", "Notificatierouteringcomponent"),
                    ("zrc", "Zaakregistratiecomponent"),
                    ("ztc", "Zaaktypecatalogus"),
                    ("drc", "Documentregistratiecomponent"),
                    ("brc", "Besluitregistratiecomponent"),
                    ("kic", "Klantinteractiescomponent"),
                ],
                help_text="Component waarop autorisatie van toepassing is.",
                max_length=50,
                verbose_name="component",
            ),
        ),
    ]
