# Seed migration: inserts required Brand records before expedientes.0007
# depends on 0003 (min_margin_alert_pct already added)
from django.db import migrations


BRANDS = [
    {"slug": "MARLUVAS", "name": "Marluvas", "brand_type": "client", "is_active": True},
    {"slug": "RW",       "name": "Rock & Walk", "brand_type": "own",    "is_active": True},
]


def seed_brands(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    for data in BRANDS:
        Brand.objects.get_or_create(slug=data["slug"], defaults=data)


def unseed_brands(apps, schema_editor):
    # Only remove if they have no related expedientes (safe rollback)
    Brand = apps.get_model("brands", "Brand")
    for data in BRANDS:
        Brand.objects.filter(slug=data["slug"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("brands", "0003_brand_min_margin_alert_pct"),
    ]

    operations = [
        migrations.RunPython(seed_brands, unseed_brands),
    ]
