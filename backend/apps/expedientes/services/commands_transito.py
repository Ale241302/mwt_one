from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import ArtifactMissingError
from .helpers import _has_artifact

def handle_c12(expediente, payload):
    # Confirmar Arribo CR (C12) -> DESTINO
    # Requirement: ART-09 (BL/China Exit confirmation)
    if not _has_artifact(expediente, 'ART-09'):
        raise ArtifactMissingError("C12 requires ART-09 (International Shipping doc).")
