# Generated manually — Sprint 23, S23-02
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0001_initial_rebate_program'),
        ('clientes', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RebateAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('custom_threshold_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('custom_threshold_units', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('rebate_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='commercial.rebateprogram')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rebate_assignments', to='clientes.cliente')),
                ('subsidiary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rebate_assignments', to='clientes.clientsubsidiary')),
            ],
            options={'db_table': 'commercial_rebate_assignment'},
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('client__isnull', False), ('subsidiary__isnull', True)),
                    models.Q(('client__isnull', True), ('subsidiary__isnull', False)),
                    _connector='OR',
                ),
                name='rebate_assignment_one_level_only',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, client__isnull=False),
                fields=['rebate_program', 'client'],
                name='rebate_assignment_unique_active_program_client',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, subsidiary__isnull=False),
                fields=['rebate_program', 'subsidiary'],
                name='rebate_assignment_unique_active_program_subsidiary',
            ),
        ),
        migrations.CreateModel(
            name='RebateLedger',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('status', models.CharField(choices=[('accruing', 'Accruing'), ('pending_review', 'Pending Review'), ('liquidated', 'Liquidated'), ('cancelled', 'Cancelled')], default='accruing', max_length=20)),
                ('accrued_amount', models.DecimalField(decimal_places=4, default=0, max_digits=14)),
                ('qualifying_amount', models.DecimalField(decimal_places=4, default=0, max_digits=14)),
                ('qualifying_units', models.PositiveIntegerField(default=0)),
                ('threshold_met', models.BooleanField(default=False)),
                ('liquidation_type', models.CharField(blank=True, choices=[('credit_note', 'Credit Note'), ('bank_transfer', 'Bank Transfer'), ('product_credit', 'Product Credit')], max_length=20, null=True)),
                ('liquidated_at', models.DateTimeField(blank=True, null=True)),
                ('rebate_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ledgers', to='commercial.rebateassignment')),
                ('liquidated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='liquidated_ledgers', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'commercial_rebate_ledger', 'ordering': ['-period_start'], 'unique_together': {('rebate_assignment', 'period_start', 'period_end')}},
        ),
        migrations.CreateModel(
            name='RebateAccrualEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proforma_id', models.CharField(max_length=100)),
                ('qualifying_amount', models.DecimalField(decimal_places=4, max_digits=14)),
                ('qualifying_units', models.PositiveIntegerField(default=0)),
                ('accrued_amount', models.DecimalField(decimal_places=4, max_digits=14)),
                ('proforma_date', models.DateField()),
                ('ledger', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accrual_entries', to='commercial.rebateledger')),
            ],
            options={'db_table': 'commercial_rebate_accrual_entry', 'ordering': ['-proforma_date'], 'unique_together': {('ledger', 'proforma_id')}},
        ),
    ]
