# Sprint 18 - Additive fields: brand_sku, pricelist_used, base_price,
# moq_per_size, credit_status, credit_released, credit_exposure,
# EventLog new fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '__first__'),
        ('brands', '__first__'),
        ('pricing', '__first__'),
    ]

    operations = [
        # T0.2: brand_sku FK nullable en ExpedienteProductLine
        migrations.AddField(
            model_name='expedienteproductline',
            name='brand_sku',
            field=models.ForeignKey(
                'brands.BrandSKU',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='expediente_lines',
                help_text='SKU especifico con talla. Nullable para backward compat.'
            ),
        ),
        # T0.4a: pricelist_used en ExpedienteProductLine
        migrations.AddField(
            model_name='expedienteproductline',
            name='pricelist_used',
            field=models.ForeignKey(
                'pricing.PriceList',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='product_lines_snapshot',
                help_text='Snapshot de la lista de precios usada al crear la linea'
            ),
        ),
        # T0.4b: base_price en ExpedienteProductLine
        migrations.AddField(
            model_name='expedienteproductline',
            name='base_price',
            field=models.DecimalField(
                max_digits=10, decimal_places=2,
                null=True, blank=True,
                help_text='Snapshot del precio base de la lista de precios'
            ),
        ),
        # T0.4d: credit_status en ExpedientePago
        migrations.AddField(
            model_name='expedientepago',
            name='credit_status',
            field=models.CharField(
                max_length=20, null=True, blank=True,
                choices=[
                    ('PENDING', 'Pending'),
                    ('CONFIRMED', 'Confirmed'),
                    ('REJECTED', 'Rejected'),
                ],
                default='PENDING',
                help_text='Estado de confirmacion del pago para liberacion de credito'
            ),
        ),
        # T0.4e: credit_released en Expediente (BooleanField, NO null)
        migrations.AddField(
            model_name='expediente',
            name='credit_released',
            field=models.BooleanField(
                default=False,
                help_text='True cuando credit_exposure <= 0. SOLO lo setea recalculate_expediente_credit().'
            ),
        ),
        # T0.4f: credit_exposure en Expediente
        migrations.AddField(
            model_name='expediente',
            name='credit_exposure',
            field=models.DecimalField(
                max_digits=12, decimal_places=2,
                null=True, blank=True,
                help_text='Exposure calculado = total_lines - total_pagos_confirmados'
            ),
        ),
        # T1.11: EventLog previous_status y new_status (event_type ya existe)
        migrations.AddField(
            model_name='eventlog',
            name='previous_status',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='eventlog',
            name='new_status',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
    ]
