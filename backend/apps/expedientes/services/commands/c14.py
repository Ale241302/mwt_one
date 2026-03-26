from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.exceptions import ArtifactMissingError, CreditBlockedError
from ..helpers import _get_rule_count, _check_credit_gate


def handle_c14(expediente, payload, env=None):
    """EmitirFactura / Finalizar Expediente (CERRADO).

    Gate: Todos los artefactos requeridos completados.
    S16-02: Verifica override de crédito si expediente bloqueado.
    S16-02: Dispara reloj de crédito si start_event == 'on_invoice'.
    """
    # S16-02: Gate de crédito
    _check_credit_gate(expediente, 'C14')

    # Gate de artefactos: verificar requeridos por la política de la marca
    required_count = _get_rule_count(expediente)
    completed_count = expediente.artifacts.filter(status=ArtifactStatusEnum.COMPLETED).count()
    if completed_count < required_count:
        raise ArtifactMissingError(
            f"C14 requiere {required_count} artefactos completados. "
            f"Solo hay {completed_count}."
        )

    # S16-02: Reloj de crédito si start_event == 'on_invoice'
    # TODO: CEO_INPUT_REQUIRED — CreditClockRule reglas por freight_mode (S16-09)
    freight_mode = getattr(expediente, 'freight_mode', 'SEA') or 'SEA'
    brand = expediente.brand

    start_event = 'on_arrival'  # Fallback seguro
    try:
        from apps.agreements.models import CreditClockRule
        rule = CreditClockRule.objects.filter(
            brand=brand,
            freight_mode=freight_mode
        ).first()
        if rule:
            start_event = rule.start_event
    except Exception:
        pass

    if start_event == 'on_invoice':
        from django.utils import timezone
        if not expediente.credit_clock_started_at:
            expediente.credit_clock_started_at = timezone.now()
            expediente.save(update_fields=['credit_clock_started_at'])

    # Transición a CERRADO (el executor principal lo persiste)
    expediente.status = ExpedienteStatus.CERRADO

    return {
        "message": "Expediente cerrado exitosamente",
        "credit_clock_trigger": start_event
    }
