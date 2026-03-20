from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import ArtifactMissingError
from .helpers import _has_artifact

def handle_c6(expediente, payload):
    # Finalizar Producción (C6) -> PREPARACION
    # Check for ART-02 and ART-03 again (just in case)
    if not _has_artifact(expediente, 'ART-02') or not _has_artifact(expediente, 'ART-03'):
        raise ArtifactMissingError("C6 requires both ART-02 and ART-03.")
