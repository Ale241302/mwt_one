# State-only migration: retargets Node and Transfer FKs
# from expedientes.LegalEntity -> core.LegalEntity in Django's migration state.
# No DB changes needed (already done by expedientes 0008 RunSQL).
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transfers', '0001_initial'),
        ('expedientes', '0009_retarget_legalentity_fks_to_core'),
        ('core', '0002_legalentity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='node',
                    name='legal_entity',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='nodes',
                        to='core.legalentity',
                    ),
                ),
                migrations.AlterField(
                    model_name='transfer',
                    name='ownership_after',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='transfers_ownership_after',
                        to='core.legalentity',
                    ),
                ),
                migrations.AlterField(
                    model_name='transfer',
                    name='ownership_before',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='transfers_ownership_before',
                        to='core.legalentity',
                    ),
                ),
            ],
        ),
    ]
