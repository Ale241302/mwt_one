# State-only migration: retargets Expediente FKs (client, legal_entity)
# from expedientes.LegalEntity -> core.LegalEntity in Django's migration state.
# No DB changes needed (already done by 0008_legalentity_to_core RunSQL).
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0008_legalentity_to_core'),
        ('core', '0002_legalentity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='expediente',
                    name='client',
                    field=models.ForeignKey(
                        help_text='Cliente',
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='expedientes_como_cliente',
                        to='core.legalentity',
                    ),
                ),
                migrations.AlterField(
                    model_name='expediente',
                    name='legal_entity',
                    field=models.ForeignKey(
                        help_text='Entidad emisora',
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='expedientes_emitidos',
                        to='core.legalentity',
                    ),
                ),
            ],
        ),
    ]
