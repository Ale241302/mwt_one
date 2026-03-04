"""
Sprint 5 — Migration: adds Sprint 5 fields (transfer FK, nodo_destino).
Also syncs Sprint 4 state-only changes not properly recorded in migration files.

NOTE: Depends on 0004 (last migration with a file in this build).
0005_costline_visibility_and_more and 0005_logisticsoption are in the DB
but have no migration files — we include their model state changes here
wrapped in SeparateDatabaseAndState (no DB ops).
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    # Depend on 0004 (last migration file that exists)
    # replaces the two 0005 migrations that are in DB but lost their files
    replaces = [
        ('expedientes', '0005_costline_visibility_and_more'),
        ('expedientes', '0005_logisticsoption'),
        ('expedientes', '0006_costline_transfer_costline_visibility_and_more'),
    ]

    dependencies = [
        ('expedientes', '0004_alter_eventlog_aggregate_type_and_more'),
        ('transfers', '0001_initial'),
    ]

    operations = [
        # ── Sprint 4 schema that already exists in DB (state-only) ──
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # From 0005_costline_visibility_and_more
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
                # From 0005_logisticsoption
                migrations.CreateModel(
                    name='LogisticsOption',
                    fields=[
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('logistics_option_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('artifact_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logistics_options', to='expedientes.artifactinstance')),
                        ('option_id', models.CharField(max_length=50)),
                        ('mode', models.CharField(choices=[('air', 'Air'), ('sea', 'Sea'), ('land', 'Land'), ('multimodal', 'Multimodal')], max_length=20)),
                        ('carrier', models.CharField(max_length=100)),
                        ('route', models.CharField(max_length=200)),
                        ('estimated_days', models.IntegerField()),
                        ('estimated_cost', models.DecimalField(decimal_places=2, max_digits=12)),
                        ('currency', models.CharField(help_text='ISO 4217', max_length=3)),
                        ('valid_until', models.DateField(blank=True, null=True)),
                        ('source', models.CharField(choices=[('manual', 'Manual'), ('api', 'API')], default='manual', max_length=20)),
                        ('is_selected', models.BooleanField(default=False)),
                    ],
                    options={
                        'verbose_name': 'Logistics Option',
                        'verbose_name_plural': 'Logistics Options',
                        'ordering': ['-created_at'],
                    },
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
