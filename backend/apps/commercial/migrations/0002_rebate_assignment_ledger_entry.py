# Sprint 23 S23-02 — regenerado para coincidir con models.py
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0001_initial_rebate_program'),
        ('clientes', '__first__'),
        ('expedientes', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RebateAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('custom_threshold_value', models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rebate_program', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='commercial.rebateprogram')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='clientes.cliente')),
                ('subsidiary', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='clientes.clientsubsidiary')),
            ],
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(client__isnull=False, subsidiary__isnull=True) |
                    models.Q(client__isnull=True, subsidiary__isnull=False)
                ),
                name='rebate_assignment_one_level_only',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, client__isnull=False),
                fields=['rebate_program', 'client'],
                name='rebate_assignment_unique_active_client',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, subsidiary__isnull=False),
                fields=['rebate_program', 'subsidiary'],
                name='rebate_assignment_unique_active_subsidiary',
            ),
        ),
        migrations.CreateModel(
            name='RebateLedger',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('status', models.CharField(
                    choices=[
                        ('accruing', 'Accruing'),
                        ('pending_review', 'Pending Review'),
                        ('liquidated', 'Liquidated'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='accruing',
                    max_length=20,
                )),
                ('accrued_rebate', models.DecimalField(decimal_places=4, default=0, max_digits=14)),
                ('liquidation_type', models.CharField(blank=True, max_length=30, null=True)),
                ('liquidated_at', models.DateTimeField(blank=True, null=True)),
                ('rebate_assignment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='commercial.rebateassignment')),
                ('liquidated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'unique_together': {('rebate_assignment', 'period_start', 'period_end')},
            },
        ),
        migrations.CreateModel(
            name='RebateAccrualEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('qualifying_amount', models.DecimalField(decimal_places=4, max_digits=14)),
                ('qualifying_units', models.DecimalField(decimal_places=4, max_digits=14)),
                ('rebate_amount', models.DecimalField(decimal_places=4, max_digits=14)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rebate_ledger', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='entries',
                    to='commercial.rebateledger',
                )),
                ('factory_order', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='rebate_accrual_entries',
                    to='expedientes.factoryorder',
                )),
            ],
            options={
                'unique_together': {('rebate_ledger', 'factory_order')},
            },
        ),
    ]
