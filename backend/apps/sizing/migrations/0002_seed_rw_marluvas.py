# Seed migration Sprint 18 - RW_S1_S6 y BR_CALZADO_33_48
from django.db import migrations


RW_DATA = {
    'S1': {'EU': '35', 'US_MEN': '3.5', 'US_WOMEN': '5', 'UK_MEN': '3', 'BR': '33', 'CM': '22.5'},
    'S2': {'EU': '36', 'US_MEN': '4',   'US_WOMEN': '5.5', 'UK_MEN': '3.5', 'BR': '34', 'CM': '23'},
    'S3': {'EU': '37', 'US_MEN': '4.5', 'US_WOMEN': '6',   'UK_MEN': '4',   'BR': '35', 'CM': '23.5'},
    'S4': {'EU': '38', 'US_MEN': '5.5', 'US_WOMEN': '7',   'UK_MEN': '5',   'BR': '36', 'CM': '24.5'},
    'S5': {'EU': '39', 'US_MEN': '6',   'US_WOMEN': '7.5', 'UK_MEN': '5.5', 'BR': '37', 'CM': '25'},
    'S6': {'EU': '40', 'US_MEN': '7',   'US_WOMEN': '8.5', 'UK_MEN': '6.5', 'BR': '38', 'CM': '25.5'},
}

BR_DATA = {
    '33': {'EU': '33', 'US_MEN': '1',   'UK_MEN': '0.5', 'CM': '21'},
    '34': {'EU': '34', 'US_MEN': '2',   'UK_MEN': '1.5', 'CM': '21.5'},
    '35': {'EU': '35', 'US_MEN': '3',   'UK_MEN': '2.5', 'CM': '22'},
    '36': {'EU': '36', 'US_MEN': '4',   'UK_MEN': '3.5', 'CM': '22.5'},
    '37': {'EU': '37', 'US_MEN': '4.5', 'UK_MEN': '4',   'CM': '23.5'},
    '38': {'EU': '38', 'US_MEN': '5.5', 'UK_MEN': '5',   'CM': '24'},
    '39': {'EU': '39', 'US_MEN': '6',   'UK_MEN': '5.5', 'CM': '24.5'},
    '40': {'EU': '40', 'US_MEN': '7',   'UK_MEN': '6.5', 'CM': '25.5'},
    '41': {'EU': '41', 'US_MEN': '7.5', 'UK_MEN': '7',   'CM': '26'},
    '42': {'EU': '42', 'US_MEN': '8.5', 'UK_MEN': '8',   'CM': '27'},
    '43': {'EU': '43', 'US_MEN': '9.5', 'UK_MEN': '9',   'CM': '27.5'},
    '44': {'EU': '44', 'US_MEN': '10',  'UK_MEN': '9.5', 'CM': '28'},
    '45': {'EU': '45', 'US_MEN': '11',  'UK_MEN': '10.5','CM': '29'},
    '46': {'EU': '46', 'US_MEN': '12',  'UK_MEN': '11.5','CM': '30'},
    '47': {'EU': '47', 'US_MEN': '12.5','UK_MEN': '12',  'CM': '30.5'},
    '48': {'EU': '48', 'US_MEN': '13',  'UK_MEN': '12.5','CM': '31'},
}


def seed_sizing(apps, schema_editor):
    SizeSystem = apps.get_model('sizing', 'SizeSystem')
    SizeDimension = apps.get_model('sizing', 'SizeDimension')
    SizeEntry = apps.get_model('sizing', 'SizeEntry')
    SizeEquivalence = apps.get_model('sizing', 'SizeEquivalence')
    BrandSizeSystemAssignment = apps.get_model('sizing', 'BrandSizeSystemAssignment')

    # --- RW_S1_S6 ---
    rw_system, _ = SizeSystem.objects.get_or_create(
        code='RW_S1_S6',
        defaults={'category': 'FOOTWEAR', 'description': 'Rana Walk S1-S6', 'is_active': True}
    )
    rw_dims = {}
    for order, std in enumerate(['EU', 'US_MEN', 'US_WOMEN', 'UK_MEN', 'BR', 'CM'], start=1):
        dim, _ = SizeDimension.objects.get_or_create(
            system=rw_system, code=std,
            defaults={'display_name': std, 'display_order': order, 'is_primary': (std == 'EU')}
        )
        rw_dims[std] = dim

    for order, (label, equivs) in enumerate(RW_DATA.items(), start=1):
        entry, _ = SizeEntry.objects.get_or_create(
            system=rw_system, label=label,
            defaults={'display_order': order, 'is_active': True}
        )
        for std, val in equivs.items():
            SizeEquivalence.objects.get_or_create(
                entry=entry, standard_system=std, value=val,
                defaults={'display_order': list(equivs.keys()).index(std) + 1, 'is_primary': (std == 'EU')}
            )

    # --- BR_CALZADO_33_48 ---
    br_system, _ = SizeSystem.objects.get_or_create(
        code='BR_CALZADO_33_48',
        defaults={'category': 'FOOTWEAR', 'description': 'Marluvas 33-48', 'is_active': True}
    )
    br_dims = {}
    for order, std in enumerate(['EU', 'US_MEN', 'UK_MEN', 'CM'], start=1):
        dim, _ = SizeDimension.objects.get_or_create(
            system=br_system, code=std,
            defaults={'display_name': std, 'display_order': order, 'is_primary': (std == 'EU')}
        )
        br_dims[std] = dim

    for order, (label, equivs) in enumerate(BR_DATA.items(), start=1):
        entry, _ = SizeEntry.objects.get_or_create(
            system=br_system, label=label,
            defaults={'display_order': order, 'is_active': True}
        )
        for std, val in equivs.items():
            SizeEquivalence.objects.get_or_create(
                entry=entry, standard_system=std, value=val,
                defaults={'display_order': list(equivs.keys()).index(std) + 1, 'is_primary': (std == 'EU')}
            )

    # --- Brand assignments (idempotente con try/except) ---
    try:
        Brand = apps.get_model('brands', 'Brand')
        rw_brand = Brand.objects.get(code='rana_walk')
        BrandSizeSystemAssignment.objects.get_or_create(
            brand=rw_brand, size_system=rw_system,
            defaults={'is_default': True}
        )
    except Exception:
        pass

    try:
        Brand = apps.get_model('brands', 'Brand')
        marluvas_brand = Brand.objects.get(code='marluvas')
        BrandSizeSystemAssignment.objects.get_or_create(
            brand=marluvas_brand, size_system=br_system,
            defaults={'is_default': True}
        )
    except Exception:
        pass


def reverse_seed(apps, schema_editor):
    SizeSystem = apps.get_model('sizing', 'SizeSystem')
    SizeSystem.objects.filter(code__in=['RW_S1_S6', 'BR_CALZADO_33_48']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sizing', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_sizing, reverse_seed),
    ]
