# Generated manually — Sprint 23, S23-01
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('brands', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='RebateProgram',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('period_type', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('semi_annual', 'Semi-Annual'), ('annual', 'Annual')], max_length=20)),
                ('valid_from', models.DateField()),
                ('valid_to', models.DateField(blank=True, null=True)),
                ('rebate_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')], max_length=20)),
                ('rebate_value', models.DecimalField(decimal_places=4, max_digits=10)),
                ('calculation_base', models.CharField(blank=True, choices=[('invoiced', 'Invoiced Price'), ('list_price', 'List Price')], max_length=20, null=True)),
                ('threshold_type', models.CharField(choices=[('amount', 'Amount'), ('units', 'Units'), ('none', 'None')], max_length=10)),
                ('threshold_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('threshold_units', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rebate_programs', to='brands.brand')),
            ],
            options={'db_table': 'commercial_rebate_program', 'ordering': ['-valid_from']},
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(('valid_to__isnull', True), ('valid_to__gte', models.F('valid_from')), _connector='OR'),
                name='rebate_program_valid_to_gte_valid_from',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('threshold_type', 'amount'), ('threshold_amount__isnull', False)),
                    models.Q(('threshold_type', 'amount'), ('threshold_amount__isnull', True)),
                    models.Q(('threshold_type__in', ['units', 'none']), ('threshold_amount__isnull', True)),
                    _connector='OR',
                ),
                name='rebate_program_amount_only_when_type_amount',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('threshold_type', 'units'), ('threshold_units__isnull', False)),
                    models.Q(('threshold_type', 'units'), ('threshold_units__isnull', True)),
                    models.Q(('threshold_type__in', ['amount', 'none']), ('threshold_units__isnull', True)),
                    _connector='OR',
                ),
                name='rebate_program_units_only_when_type_units',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('threshold_type', 'none'), _negated=True),
                    models.Q(('threshold_type', 'none'), ('threshold_amount__isnull', True), ('threshold_units__isnull', True)),
                    _connector='OR',
                ),
                name='rebate_program_none_no_thresholds',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('threshold_type', 'amount'), _negated=True),
                    models.Q(('threshold_type', 'amount'), ('threshold_units__isnull', True)),
                    _connector='OR',
                ),
                name='rebate_program_amount_excludes_units',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('threshold_type', 'units'), _negated=True),
                    models.Q(('threshold_type', 'units'), ('threshold_amount__isnull', True)),
                    _connector='OR',
                ),
                name='rebate_program_units_excludes_amount',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(rebate_value__gt=0),
                name='rebate_program_value_positive',
            ),
        ),
        migrations.CreateModel(
            name='RebateProgramProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_key', models.CharField(max_length=50)),
                ('rebate_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_inclusions', to='commercial.rebateprogram')),
            ],
            options={'db_table': 'commercial_rebate_program_product', 'unique_together': {('rebate_program', 'product_key')}},
        ),
    ]
