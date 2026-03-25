from apps.expedientes.exceptions import ArtifactMissingError, CreditBlockedError
from ..helpers import _has_artifact, _check_credit_gate


def handle_c8(expediente, payload):
    """Cargar Factura Comercial (ART-07): registra la factura comercial del proveedor.

    Gate: ART-06 (Packing List) requerido.
    S16-02: Verifica override de crédito si expediente bloqueado.
    """
    # S16-02: Gate de crédito
    _check_credit_gate(expediente, 'C8')

    # Gate de artefactos: ART-06 Packing List
    if not _has_artifact(expediente, 'ART-06'):
        raise ArtifactMissingError("C8 requiere ART-06 (Packing List).")

    return {"message": "Factura Comercial registrada exitosamente"}
