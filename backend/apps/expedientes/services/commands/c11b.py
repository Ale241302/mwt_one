from ..helpers import _has_artifact
from apps.expedientes.exceptions import CommandValidationError

def handle_c11b(expediente, payload, env=None):
    """S17-02: Confirmar Salida (DESPACHO -> TRANSITO).
    Gate: ART-06 (Packing List) must be present.
    """
    if not _has_artifact(expediente, 'ART-06'):
        raise CommandValidationError("Se requiere Packing List (ART-06) para confirmar salida.")
    
    # S16-01: Trigger clock on departure if configured
    from ..helpers import _trigger_credit_clock
    _trigger_credit_clock(expediente, 'on_departure')
        
    return {"message": "Salida confirmada, transito iniciado."}
