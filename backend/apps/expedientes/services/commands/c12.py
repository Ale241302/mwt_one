"""C12 — ConfirmarArribo CR.

S16-02: Dispara reloj de crédito si CreditClockRule.start_event == 'on_arrival'.
Gate: ART-09 (International Shipping document).
"""
from django.utils import timezone
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.exceptions import ArtifactMissingError
from ..helpers import _has_artifact


def handle_c12(expediente, payload, env=None):
    """C12: Confirmar Arribo CR.

    Gate: ART-09 presente.
    S16-02: trigger_credit_clock si start_event == 'on_arrival'.
    """
    if not _has_artifact(expediente, 'ART-09'):
        raise ArtifactMissingError("C12 requires ART-09 (International Shipping document).")

    # S16-02: Trigger credit clock if start_event == 'on_arrival'
    from ..helpers import _trigger_credit_clock
    clock_triggered = _trigger_credit_clock(expediente, 'on_arrival')

    # S16-03: Ensure we don't accidentally close the clock here. 
    # Closing only happens in C14 or if explicit conditions are met with ART-10.
    
    return {
        "message": "Arrival at destination confirmed",
        "credit_clock_triggered": clock_triggered,
    }
