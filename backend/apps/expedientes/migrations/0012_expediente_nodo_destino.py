# 0012 – nodo_destino column already exists in DB; mark state only.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0011_costline_amount_base_currency_costline_base_currency_and_more'),
        ('transfers', '0002_retarget_legalentity_fks_to_core'),
    ]

    operations = [
        # The column already exists in the database; we only update Django's
        # migration state so subsequent makemigrations stays clean.
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # no DDL executed
            state_operations=[
                migrations.AddField(
                    model_name='expediente',
                    name='nodo_destino',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='Target node (triggers transfer suggestion on close)',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='expedientes_destino',
                        to='transfers.node',
                    ),
                ),
            ],
        ),
    ]
