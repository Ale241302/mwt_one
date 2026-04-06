# Sprint 23 refactor — aligns DB schema with updated models.py
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0004_brand_artifact_policy_version'),
        ('brands', '__first__'),
        ('clientes', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── 1. RebateProgram ──────────────────────────────────────────────────
        # Remove old constraints
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_valid_to_gte_valid_from'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_amount_only_when_type_amount'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_units_only_when_type_units'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_none_no_thresholds'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_amount_excludes_units'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_units_excludes_amount'),
        migrations.RemoveConstraint(model_name='rebateprogram', name='rebate_program_value_positive'),

        # Remove old threshold fields
        migrations.RemoveField(model_name='rebateprogram', name='threshold_amount'),
        migrations.RemoveField(model_name='rebateprogram', name='threshold_units'),

        # Remove updated_at
        migrations.RemoveField(model_name='rebateprogram', name='updated_at'),

        # Add threshold_value
        migrations.AddField(
            model_name='rebateprogram',
            name='threshold_value',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),

        # Update period_type choices
        migrations.AlterField(
            model_name='rebateprogram',
            name='period_type',
            field=models.CharField(
                choices=[('quarterly', 'Quarterly'), ('annual', 'Annual')],
                max_length=20,
            ),
        ),

        # Update brand FK to PROTECT
        migrations.AlterField(
            model_name='rebateprogram',
            name='brand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='brands.brand'),
        ),

        # Update calculation_base choices label
        migrations.AlterField(
            model_name='rebateprogram',
            name='calculation_base',
            field=models.CharField(
                blank=True,
                choices=[('invoiced', 'Invoiced'), ('list_price', 'List Price')],
                max_length=20,
                null=True,
            ),
        ),

        # Rename table (remove db_table override)
        migrations.AlterModelTable(model_name='rebateprogram', table=None),

        # Add new constraints
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=models.F('valid_from')),
                name='rebate_valid_to_gte_valid_from',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=~models.Q(threshold_type__in=['amount', 'units']) | models.Q(threshold_value__isnull=False),
                name='rebate_threshold_value_required',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=~models.Q(threshold_type='none') | models.Q(threshold_value__isnull=True),
                name='rebate_threshold_value_null_when_none',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=models.Q(rebate_value__gt=0),
                name='rebate_value_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=~models.Q(rebate_type='percentage') | models.Q(rebate_value__lte=100),
                name='rebate_percentage_max_100',
            ),
        ),
        migrations.AddConstraint(
            model_name='rebateprogram',
            constraint=models.CheckConstraint(
                check=~models.Q(rebate_type='fixed_amount') | models.Q(calculation_base__isnull=True),
                name='rebate_fixed_no_calc_base',
            ),
        ),

        # ── 2. RebateProgramProduct ───────────────────────────────────────────
        # Drop UUID id → replace with BigAutoField via recreating the model
        # First remove old unique_together so we can drop the table cleanly
        migrations.AlterUniqueTogether(model_name='rebateprogramproduct', unique_together=set()),
        migrations.DeleteModel(name='RebateProgramProduct'),
        migrations.CreateModel(
            name='RebateProgramProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_key', models.CharField(max_length=100)),
                ('rebate_program', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='products',
                    to='commercial.rebateprogram',
                )),
            ],
            options={
                'unique_together': {('rebate_program', 'product_key')},
            },
        ),

        # ── 3. CommissionRule ─────────────────────────────────────────────────
        # Remove old constraints
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_one_level_only'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_value_positive'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_brand_default'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_brand_product'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_client_default'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_client_product'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_subsidiary_default'),
        migrations.RemoveConstraint(model_name='commissionrule', name='commission_rule_unique_active_subsidiary_product'),

        # Remove updated_at
        migrations.RemoveField(model_name='commissionrule', name='updated_at'),

        # Rename fields
        migrations.RenameField(model_name='commissionrule', old_name='rule_type', new_name='commission_type'),
        migrations.RenameField(model_name='commissionrule', old_name='rule_value', new_name='commission_value'),

        # Update product_key max_length
        migrations.AlterField(
            model_name='commissionrule',
            name='product_key',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),

        # Update FKs to PROTECT
        migrations.AlterField(
            model_name='commissionrule',
            name='brand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='commission_rules', to='brands.brand'),
        ),
        migrations.AlterField(
            model_name='commissionrule',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='commission_rules', to='clientes.cliente'),
        ),
        migrations.AlterField(
            model_name='commissionrule',
            name='subsidiary',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='commission_rules', to='clientes.clientsubsidiary'),
        ),

        # Rename table (remove db_table override)
        migrations.AlterModelTable(model_name='commissionrule', table=None),

        # Add new constraints
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.CheckConstraint(
                check=(
                    (models.Q(brand__isnull=False) & models.Q(client__isnull=True) & models.Q(subsidiary__isnull=True)) |
                    (models.Q(brand__isnull=True) & models.Q(client__isnull=False) & models.Q(subsidiary__isnull=True)) |
                    (models.Q(brand__isnull=True) & models.Q(client__isnull=True) & models.Q(subsidiary__isnull=False))
                ),
                name='commission_one_level_only',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, product_key__isnull=True, client__isnull=True, subsidiary__isnull=True),
                fields=['brand'],
                name='unique_active_brand_default_commission',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, client__isnull=True, subsidiary__isnull=True, product_key__isnull=False),
                fields=['brand', 'product_key'],
                name='unique_active_brand_product_commission',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, product_key__isnull=True, brand__isnull=True, subsidiary__isnull=True),
                fields=['client'],
                name='unique_active_client_default_commission',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, brand__isnull=True, subsidiary__isnull=True, product_key__isnull=False),
                fields=['client', 'product_key'],
                name='unique_active_client_product_commission',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, product_key__isnull=True, brand__isnull=True, client__isnull=True),
                fields=['subsidiary'],
                name='unique_active_subsidiary_default_commission',
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionrule',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True, brand__isnull=True, client__isnull=True, product_key__isnull=False),
                fields=['subsidiary', 'product_key'],
                name='unique_active_subsidiary_product_commission',
            ),
        ),

        # ── 4. BrandArtifactPolicyVersion ─────────────────────────────────────
        # Remove old constraints
        migrations.RemoveConstraint(model_name='brandartifactpolicyversion', name='artifact_policy_unique_active_per_brand'),
        migrations.RemoveConstraint(model_name='brandartifactpolicyversion', name='artifact_policy_unique_version_per_brand'),

        # Remove fields no longer in model
        migrations.RemoveField(model_name='brandartifactpolicyversion', name='notes'),
        migrations.RemoveField(model_name='brandartifactpolicyversion', name='updated_at'),

        # Add created_by
        migrations.AddField(
            model_name='brandartifactpolicyversion',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # Update brand FK to PROTECT
        migrations.AlterField(
            model_name='brandartifactpolicyversion',
            name='brand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='artifact_policy_versions', to='brands.brand'),
        ),

        # Update artifact_policy (remove help_text)
        migrations.AlterField(
            model_name='brandartifactpolicyversion',
            name='artifact_policy',
            field=models.JSONField(),
        ),

        # Update is_active default (False → True)
        migrations.AlterField(
            model_name='brandartifactpolicyversion',
            name='is_active',
            field=models.BooleanField(default=True),
        ),

        # Update superseded_by (remove help_text)
        migrations.AlterField(
            model_name='brandartifactpolicyversion',
            name='superseded_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='supersedes',
                to='commercial.brandartifactpolicyversion',
            ),
        ),

        # Rename table (remove db_table override)
        migrations.AlterModelTable(model_name='brandartifactpolicyversion', table=None),

        # Add new constraints
        migrations.AddConstraint(
            model_name='brandartifactpolicyversion',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=['brand'],
                name='brand_artifact_policy_one_active_per_brand',
            ),
        ),
        migrations.AddConstraint(
            model_name='brandartifactpolicyversion',
            constraint=models.UniqueConstraint(
                fields=['brand', 'version'],
                name='brand_artifact_policy_unique_version',
            ),
        ),

        # ── 5. RebateAccrualEntry ─────────────────────────────────────────────
        # Fix unique_together: was (rebate_ledger, factory_order), now (ledger, factory_order)
        migrations.AlterUniqueTogether(model_name='rebateaccrualentry', unique_together=set()),

        # Rename rebate_ledger → ledger
        migrations.RenameField(model_name='rebateaccrualentry', old_name='rebate_ledger', new_name='ledger'),

        # Restore unique_together with new field name
        migrations.AlterUniqueTogether(
            model_name='rebateaccrualentry',
            unique_together={('ledger', 'factory_order')},
        ),

        # ── 6. Clientes app ───────────────────────────────────────────────────
        migrations.AddField(
            model_name='clientsubsidiary',
            name='payment_grace_days',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
