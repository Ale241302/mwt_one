from django.utils import timezone
from apps.expedientes.enums_exp import CreditClockStartRule
from apps.expedientes.exceptions import ArtifactMissingError
from ..helpers import _has_artifact

def handle_c11(expediente, payload):
    """Confirmar Salida Aduana (China). Triggers Credit Clock if ON_SHIPMENT."""
    if not _has_artifact(expediente, 'ART-06'):
        raise ArtifactMissingError("C11 requires ART-06 (Packing List).")
    if not _has_artifact(expediente, 'ART-07'):
        raise ArtifactMissingError("C11 requires ART-07 (Commercial Invoice).")

    # S16-02: Credit clock starts on shipment if rule is ON_SHIPMENT
    if expediente.credit_clock_start_rule == CreditClockStartRule.ON_SHIPMENT:
        if not expediente.credit_clock_started_at:
            expediente.credit_clock_started_at = timezone.now()
            # We don't save here because the dispatcher usually handles saving or
            # the caller does. But for clarity:
            expediente.save(update_fields=['credit_clock_started_at'])

    return {"message": "Shipment confirmed, credit clock started if applicable"}
