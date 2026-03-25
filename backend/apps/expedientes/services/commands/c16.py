"""C16 — CerrarExpediente (Cierre definitivo).

S16-02: Libera CreditExposure.reserved_amount al cerrar.
Gate: Expediente en estado CERRADO previo (C14 ejecutado).
"""
from django.utils import timezone

from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.exceptions import CommandError


def handle_c16(expediente, payload):
    """C16: Cierre definitivo del expediente.

    - Verifica que el expediente esté en estado CERRADO (C14 ya ejecutado).
    - Libera CreditExposure.reserved_amount (S16-02).
    - Registra fecha de cierre definitivo.
    """
    # Gate: C14 debe haber sido ejecutado (estado CERRADO)
    if expediente.status != ExpedienteStatus.CERRADO:
        raise CommandError(
            f"C16 requiere estado CERRADO. Estado actual: {expediente.status}. "
            "Ejecute C14 (EmitirFactura) primero."
        )

    # S16-02: Liberar reserva de crédito al cerrar definitivamente
    credit_released = Decimal('0')
    try:
        from apps.agreements.models import CreditExposure
        from apps.agreements.models import CreditPolicy
        # Buscar la CreditExposure asociada al brand x subsidiary
        policy = CreditPolicy.objects.filter(
            brand=expediente.brand,
            status='active',
        ).first()
        if policy:
            exposure = CreditExposure.objects.filter(policy=policy).first()
            if exposure and exposure.reserved_amount > 0:
                # Determinar el monto a liberar (estimado del expediente)
                amount_to_release = expediente.estimated_amount or Decimal('0')
                if amount_to_release > 0:
                    released = exposure.release(amount_to_release)
                    credit_released = amount_to_release

                    # Limpiar flags de crédito del expediente
                    expediente.credit_blocked = False
                    expediente.credit_warning = False
                    expediente.save(update_fields=['credit_blocked', 'credit_warning'])
    except Exception:
        pass  # No bloquea el cierre si falla la liberación

    return {
        "message": "Expediente cerrado definitivamente",
        "credit_released": float(credit_released),
        "closed_at": timezone.now().isoformat(),
    }


# Importación diferida para evitar circular imports
from decimal import Decimal  # noqa: E402
