# Generated manually for S22-01
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0002_pricelistitem_moq_per_size'),
        ('brands', '0002_brandconfigversion_catalogversion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceListVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version_label', models.CharField(max_length=100)),
                ('storage_key', models.CharField(blank=True, default='', max_length=500)),
                ('is_active', models.BooleanField(default=False)),
                ('activated_at', models.DateTimeField(blank=True, null=True)),
                ('deactivated_at', models.DateTimeField(blank=True, null=True)),
                ('deactivation_reason', models.CharField(
                    blank=True,
                    choices=[
                        ('manual', 'Manual'),
                        ('price_decrease', 'Price Decrease'),
                        ('superseded', 'Superseded'),
                    ],
                    max_length=20,
                    null=True,
                )),
                ('notes', models.TextField(blank=True, default='')),
                ('brand', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pricelist_versions',
                    to='brands.brand',
                )),
                ('uploaded_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='uploaded_pricelists',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'pricing_pricelistversion',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PriceListGradeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reference_code', models.CharField(max_length=100)),
                ('tip_type', models.CharField(blank=True, default='', max_length=50)),
                ('insole_type', models.CharField(blank=True, default='', max_length=50)),
                ('ncm', models.CharField(blank=True, default='', max_length=20)),
                ('ca_number', models.CharField(blank=True, default='', max_length=50)),
                ('factory_code', models.CharField(blank=True, default='', max_length=50)),
                ('factory_center', models.CharField(blank=True, default='', max_length=50)),
                ('unit_price_usd', models.DecimalField(decimal_places=4, max_digits=12)),
                ('grade_label', models.CharField(blank=True, default='', max_length=50)),
                ('size_multipliers', models.JSONField(blank=True, default=dict)),
                ('pricelist_version', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='grade_items',
                    to='pricing.pricelistversion',
                )),
                ('brand_sku', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pricelist_grade_items',
                    to='brands.brandsku',
                )),
            ],
            options={
                'db_table': 'pricing_pricelistgradeitem',
                'unique_together': {('pricelist_version', 'reference_code')},
            },
        ),
    ]
