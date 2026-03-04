"""
Sprint 5 — Sync migration: records pre-existing Sprint 4 schema changes
plus adds Sprint 5 new fields (transfer FK, nodo_destino).

This migration handles a mixed state where some fields (visibility, brand
choices, artifact_type/status alters) already exist in DB from Sprint 4
but were not recorded in Django migrations.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0005_logisticsoption'),
        ('transfers', '0001_initial'),
    ]

    operations = [
        # ── Sprint 4 changes already in DB (state-only, no DB ops) ──
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='costline',
                    name='visibility',
                    field=models.CharField(
                        choices=[('internal', 'Internal'), ('client', 'Client')],
                        default='internal',
                        help_text='internal=CEO-only, client=visible to client',
                        max_length=10,
                    ),
                ),
                migrations.AlterField(
                    model_name='artifactinstance',
                    name='artifact_type',
                    field=models.CharField(
                        help_text='ART-01 to ART-19', max_length=20
                    ),
                ),
                migrations.AlterField(
                    model_name='artifactinstance',
                    name='status',
                    field=models.CharField(
                        choices=[
                            ('draft', 'Draft'),
                            ('pending', 'Pending'),
                            ('completed', 'Completed'),
                            ('superseded', 'Superseded'),
                            ('void', 'Void'),
                        ],
                        default='draft',
                        max_length=20,
                    ),
                ),
                migrations.AlterField(
                    model_name='expediente',
                    name='brand',
                    field=models.CharField(
                        choices=[
                            ('MARLUVAS', 'Marluvas'),
                            ('TECMATER', 'Tecmater'),
                        ],
                        default='MARLUVAS',
                        max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='logisticsoption',
                    name='artifact_instance',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='logistics_options',
                        to='expedientes.artifactinstance',
                    ),
                ),
            ],
            database_operations=[],
        ),

        # ── Sprint 5: NEW fields that need actual DB changes ──
        migrations.AddField(
            model_name='costline',
            name='transfer',
            field=models.ForeignKey(
                blank=True,
                help_text='XOR with expediente — use one or the other',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cost_lines',
                to='transfers.transfer',
            ),
        ),
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
        migrations.AlterField(
            model_name='costline',
            name='expediente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cost_lines',
                to='expedientes.expediente',
            ),
        ),
    ]
