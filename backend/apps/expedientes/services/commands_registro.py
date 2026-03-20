from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CommandValidationError, ArtifactMissingError
from .helpers import _has_artifact

def handle_c2(expediente, payload):
    # Registrar Proforma (ART-02)
    # Generic execution handles artifact creation if creates_art is set
    pass

def handle_c3(expediente, payload):
    # Registrar Orden de Compra (ART-03)
    pass

def handle_c4(expediente, payload):
    # Decidir Modo Import/Comision
    mode = payload.get('mode')
    if mode not in ['IMPORT', 'COMISION']:
        raise CommandValidationError(f"Invalid mode: {mode}")
    expediente.mode = mode
    expediente.save(update_fields=['mode'])

def handle_c5(expediente, payload):
    # Confirmar Registro
    if not _has_artifact(expediente, 'ART-02'):
        raise ArtifactMissingError("C5 requires ART-02 (Proforma).")
    if not _has_artifact(expediente, 'ART-03'):
        raise ArtifactMissingError("C5 requires ART-03 (Purchase Order).")
