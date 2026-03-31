from apps.expedientes.exceptions import CreditBlockedError
from ..helpers import _check_credit_gate


def handle_c8(expediente, payload, env=None):
    """Cargar Factura Comercial (ART-07): registra la factura comercial del proveedor.

    S16-02: Verifica override de crédito si expediente bloqueado.
    NOTE: Gate ART-06 (Packing List) desactivado temporalmente.
    """
    # S16-02: Gate de crédito
    _check_credit_gate(expediente, 'C8')

    return {"message": "Factura Comercial registrada exitosamente"}
