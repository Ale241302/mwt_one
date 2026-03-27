# Generated manually for Sprint 18 - SizeSystem app
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('brands', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SizeSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('category', models.CharField(choices=[('FOOTWEAR', 'Footwear'), ('SHIRT', 'Shirt'), ('PANTS', 'Pants'), ('GLOVES', 'Gloves'), ('GENERIC', 'Generic')], default='GENERIC', max_length=20)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='SizeDimension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30)),
                ('display_name', models.CharField(max_length=60)),
                ('unit', models.CharField(blank=True, default='', max_length=20)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_primary', models.BooleanField(default=False)),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dimensions', to='sizing.sizesystem')),
            ],
            options={'ordering': ['system', 'display_order', 'code'], 'unique_together': {('system', 'code')}},
        ),
        migrations.CreateModel(
            name='SizeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text="Etiqueta visible, ej: 'S1', '42'", max_length=20)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='sizing.sizesystem')),
            ],
            options={'ordering': ['system', 'display_order', 'label'], 'unique_together': {('system', 'label')}},
        ),
        migrations.CreateModel(
            name='SizeEntryValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=30)),
                ('dimension', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry_values', to='sizing.sizedimension')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dimension_values', to='sizing.sizeentry')),
            ],
            options={'unique_together': {('entry', 'dimension')}},
        ),
        migrations.CreateModel(
            name='SizeEquivalence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('standard_system', models.CharField(help_text="Codigo libre del sistema estandar, ej: 'EU', 'US_MEN', 'CM'", max_length=30)),
                ('value', models.CharField(max_length=30)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_primary', models.BooleanField(default=False)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equivalences', to='sizing.sizeentry')),
            ],
            options={'ordering': ['entry', 'display_order', 'standard_system'], 'unique_together': {('entry', 'standard_system', 'value')}},
        ),
        migrations.CreateModel(
            name='BrandSizeSystemAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_default', models.BooleanField(default=False)),
                ('assigned_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, default='')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='size_system_assignments', to='brands.brand')),
                ('size_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='brand_assignments', to='sizing.sizesystem')),
            ],
            options={'ordering': ['brand', '-is_default', 'size_system__code'], 'unique_together': {('brand', 'size_system')}},
        ),
    ]
