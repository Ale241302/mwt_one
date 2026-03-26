from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.exceptions import ArtifactMissingError, CreditBlockedError
from ..helpers import _has_artifact, _check_credit_gate


def handle_c6(expediente, payload, env=None):
    """Finalizar Producción (ART-05): confirma que la producción fue completada.

    Gate: ART-02 (Proforma) + ART-03 (Purchase Order) requeridos.
    S16-02: Verifica override de crédito si expediente bloqueado.
    """
    # S16-02: Gate de crédito
    _check_credit_gate(expediente, 'C6')

    # Gate de artefactos
    if not _has_artifact(expediente, 'ART-02'):
        raise ArtifactMissingError("C6 requiere ART-02 (Proforma Invoice).")
    if not _has_artifact(expediente, 'ART-03'):
        raise ArtifactMissingError("C6 requiere ART-03 (Purchase Order).")

    return {"message": "Producción finalizada exitosamente"}
