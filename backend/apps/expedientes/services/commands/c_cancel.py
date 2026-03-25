from apps.expedientes.enums_exp import ExpedienteStatus

from apps.agreements.models import CreditExposure


def handle_cancel(expediente, payload):
    """S16-03: Cancelación total con liberación de crédito."""
    # Si estaba ABIERTO, liberamos el crédito reservado
    if expediente.status == ExpedienteStatus.ABIERTO:
        exposure = CreditExposure.objects.filter(expediente=expediente).first()
        if exposure and exposure.reserved_amount > 0:
            # Liberamos todo lo reservado para este expediente
            exposure.release(exposure.reserved_amount)

    expediente.status = ExpedienteStatus.CANCELADO
    expediente.save(update_fields=['status'])
