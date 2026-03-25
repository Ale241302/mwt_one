"""C12 — ConfirmarArribo CR.

S16-02: Dispara reloj de crédito si CreditClockRule.start_event == 'on_arrival'.
Gate: ART-09 (International Shipping document).
"""
from django.utils import timezone
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.exceptions import ArtifactMissingError
from ..helpers import _has_artifact


def handle_c12(expediente, payload):
    """C12: Confirmar Arribo CR.

    Gate: ART-09 presente.
    S16-02: trigger_credit_clock si start_event == 'on_arrival'.
    """
    if not _has_artifact(expediente, 'ART-09'):
        raise ArtifactMissingError("C12 requires ART-09 (International Shipping document).")

    # S16-02: Trigger credit clock if start_event == 'on_arrival'
    # TODO: CEO_INPUT_REQUIRED — CreditClockRule por freight_mode (S16-09)
    freight_mode = getattr(expediente, 'freight_mode', 'SEA') or 'SEA'
    brand = expediente.brand

    start_event = 'on_arrival'  # Default fallback (sea = on_arrival per spec)
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

    clock_triggered = False
    if start_event == 'on_arrival' and not expediente.credit_clock_started_at:
        expediente.credit_clock_started_at = timezone.now()
        expediente.save(update_fields=['credit_clock_started_at'])
        clock_triggered = True

    return {
        "message": "Arrival at destination confirmed",
        "credit_clock_triggered": clock_triggered,
        "credit_clock_start_event": start_event,
    }
