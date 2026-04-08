# S25-01: AddField ×6 en ExpedientePago — payment status machine (structural migration)
# SOLO AddField — verificado: no hay AlterField ni RemoveField.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0022_eventlog_expediente_alter_eventlog_proforma'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='expedientepago',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pendiente verificación'),
                    ('verified', 'Verificado'),
                    ('credit_released', 'Crédito liberado'),
                    ('rejected', 'Rechazado'),
                ],
                default='pending',
                help_text=(
                    "Estado del pago dentro de su ciclo de vida. "
                    "pending → verificado por CEO → crédito liberado. "
                    "Pagos legacy (pre-S25) migrados según regla C2."
                ),
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='expedientepago',
            name='verified_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp de verificación por CEO.',
            ),
        ),
        migrations.AddField(
            model_name='expedientepago',
            name='verified_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='Usuario que verificó el pago.',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='verified_payments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='expedientepago',
            name='credit_released_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp de liberación de crédito.',
            ),
        ),
        migrations.AddField(
            model_name='expedientepago',
            name='credit_released_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='Usuario que liberó el crédito.',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='released_payments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='expedientepago',
            name='rejection_reason',
            field=models.TextField(
                blank=True,
                default='',
                help_text="Motivo de rechazo si payment_status='rejected'.",
            ),
        ),
    ]
