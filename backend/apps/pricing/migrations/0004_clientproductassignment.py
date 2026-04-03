# Generated manually for S22-02
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0003_pricelistversion_pricelistgradeitem'),
        ('brands', '0002_brandconfigversion_catalogversion'),
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientProductAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cached_client_price', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('cached_base_price', models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ('cached_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('client_subsidiary', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_assignments',
                    to='clients.clientsubsidiary',
                )),
                ('brand_sku', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='client_assignments',
                    to='brands.brandsku',
                )),
                ('cached_pricelist_version', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assignments_cached',
                    to='pricing.pricelistversion',
                )),
            ],
            options={
                'db_table': 'pricing_clientproductassignment',
                'unique_together': {('client_subsidiary', 'brand_sku')},
            },
        ),
    ]
