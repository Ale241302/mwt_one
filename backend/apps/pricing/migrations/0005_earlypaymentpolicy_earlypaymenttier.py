# Generated manually for S22-03
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0004_clientproductassignment'),
        ('brands', '0002_brandconfigversion_catalogversion'),
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EarlyPaymentPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('base_payment_days', models.PositiveIntegerField(default=90)),
                ('base_commission_pct', models.DecimalField(decimal_places=2, default='10.00', max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('client_subsidiary', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='early_payment_policies',
                    to='clientes.clientsubsidiary',
                )),
                ('brand', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='early_payment_policies',
                    to='brands.brand',
                )),
            ],
            options={
                'db_table': 'pricing_earlypaymentpolicy',
                'unique_together': {('client_subsidiary', 'brand')},
            },
        ),
        migrations.CreateModel(
            name='EarlyPaymentTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_days', models.PositiveIntegerField(help_text='Pago en X días o menos')),
                ('discount_pct', models.DecimalField(
                    decimal_places=2,
                    max_digits=5,
                    help_text='Valor positivo - se aplica como descuento. Ej. 1.75 = -1.75%',
                )),
                ('policy', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tiers',
                    to='pricing.earlypaymentpolicy',
                )),
            ],
            options={
                'db_table': 'pricing_earlypaymenttier',
                'ordering': ['-payment_days'],
                'unique_together': {('policy', 'payment_days')},
            },
        ),
    ]