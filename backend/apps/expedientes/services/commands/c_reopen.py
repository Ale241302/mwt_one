from apps.expedientes.enums_exp import ExpedienteStatus

from django.utils import timezone
from apps.expedientes.exceptions import CommandError


def handle_reopen(expediente, payload):
    """S16-03: Reapertura con restricciones: máximo 1 vez y requiere justificación."""
    if expediente.reopen_count >= 1:
        raise CommandError("El expediente ya ha sido reabierto una vez. No se permiten más reaperturas.")

    justification = payload.get('justification')
    if not justification or len(justification) < 10:
        raise CommandError("Debe proporcionar una justificación válida (mínimo 10 caracteres) para reabrir.")

    expediente.status = ExpedienteStatus.REGISTRO
    expediente.reopen_count += 1
    expediente.reopened_at = timezone.now()
    expediente.reopen_justification = justification
    expediente.save(update_fields=['status', 'reopen_count', 'reopened_at', 'reopen_justification'])
