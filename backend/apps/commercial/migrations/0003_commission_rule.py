# Generated manually — Sprint 23, S23-03
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0002_rebate_assignment_ledger_entry'),
        ('brands', '__first__'),
        ('clientes', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommissionRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_key', models.CharField(blank=True, max_length=50, null=True)),
                ('rule_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')], max_length=20)),
                ('rule_value', models.DecimalField(decimal_places=4, max_digits=10)),
                ('commission_base', models.CharField(blank=True, choices=[('sale_price', 'Sale Price'), ('gross_margin', 'Gross Margin')], max_length=20, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commission_rules', to='brands.brand')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commission_rules', to='clientes.cliente')),
                ('subsidiary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commission_rules', to='clientes.clientsubsidiary')),
            ],
            options={'db_table': 'commercial_commission_rule'},
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('brand__isnull', False), ('client__isnull', True), ('subsidiary__isnull', True)),
                    models.Q(('brand__isnull', True), ('client__isnull', False), ('subsidiary__isnull', True)),
                    models.Q(('brand__isnull', True), ('client__isnull', True), ('subsidiary__isnull', False)),
                    _connector='OR',
                ),
                name='commission_rule_one_level_only',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.CheckConstraint(
                check=models.Q(rule_value__gt=0),
                name='commission_rule_value_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, brand__isnull=False, product_key__isnull=True),
                fields=['brand'],
                name='commission_rule_unique_active_brand_default',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, brand__isnull=False, product_key__isnull=False),
                fields=['brand', 'product_key'],
                name='commission_rule_unique_active_brand_product',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, client__isnull=False, product_key__isnull=True),
                fields=['client'],
                name='commission_rule_unique_active_client_default',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, client__isnull=False, product_key__isnull=False),
                fields=['client', 'product_key'],
                name='commission_rule_unique_active_client_product',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, subsidiary__isnull=False, product_key__isnull=True),
                fields=['subsidiary'],
                name='commission_rule_unique_active_subsidiary_default',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, subsidiary__isnull=False, product_key__isnull=False),
                fields=['subsidiary', 'product_key'],
                name='commission_rule_unique_active_subsidiary_product',
            ),
        ),
    ]
