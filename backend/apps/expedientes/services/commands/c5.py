from django.utils import timezone
from apps.expedientes.exceptions import ArtifactMissingError
from ..helpers import _has_artifact
from ..pricing import assign_agreement_defaults

def handle_c5(expediente, payload):
    # Confirmar Registro
    if not _has_artifact(expediente, 'ART-02'):
        raise ArtifactMissingError("C5 requires ART-02 (Proforma).")
    if not _has_artifact(expediente, 'ART-03'):
        raise ArtifactMissingError("C5 requires ART-03 (Purchase Order).")
        
    # S14-05: Save immutable snapshot of commercial terms
    now = timezone.now()
    expediente.snapshot_commercial = {
        'snapshot_date': now.isoformat(),
        'pricing_mode': expediente.mode,
        'freight_mode': expediente.freight_mode,
        'transport_mode': expediente.transport_mode,
        'dispatch_mode': expediente.dispatch_mode,
        'credit_clock_start_rule': expediente.credit_clock_start_rule,
    }
    
    # S16-04: Automatic Pricing assignment
    assign_agreement_defaults(expediente)
    
    expediente.save(update_fields=['snapshot_commercial'])
