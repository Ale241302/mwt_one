# S25-01: Data migration legacy — migra payment_status de pagos pre-S25.
# FORWARD-ONLY. reverse=noop.
# BACKUP OBLIGATORIO de expedientes_expedientepago antes de ejecutar en producción.
#
# Regla C2 (SSOT):
#   amount <= 0 o NULL  → 'pending'
#   amount > 0 + expediente.status en GATE_PASSED_STATUSES → 'credit_released'
#   amount > 0 + expediente.status fuera de gate → 'verified'

from django.db import migrations


def forwards(apps, schema_editor):
    """
    Clasifica pagos legacy según regla C2 del LOTE_SM_SPRINT25.
    Usa apps.get_model() — NO import del model vivo (fix M2 R5 v1.5).
    Los strings de status están congelados con referencia al SSOT.
    """
    ExpedientePago = apps.get_model("expedientes", "ExpedientePago")

    # Congelados desde ENT_OPS_STATE_MACHINE FROZEN v1.2.2 — estados post-gate de crédito.
    # NO importar del model vivo: las migrations deben depender del estado histórico.
    # Si el enum cambia en el futuro, esta migración sigue siendo reproducible.
    GATE_PASSED_STATUSES = {
        "PRODUCCION", "PREPARACION", "DESPACHO",
        "TRANSITO", "EN_DESTINO", "CERRADO",
    }

    for pago in ExpedientePago.objects.select_related("expediente").iterator():
        if pago.amount_paid is None or pago.amount_paid <= 0:
            pago.payment_status = 'pending'
        elif pago.expediente.status in GATE_PASSED_STATUSES:
            pago.payment_status = 'credit_released'   # ya pasó gate de crédito → pago cuenta
        else:
            pago.payment_status = 'verified'           # CEO debe liberar manualmente
        pago.save(update_fields=['payment_status'])


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0023_add_payment_status'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
