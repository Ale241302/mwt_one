from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CommandValidationError, ArtifactMissingError
from .helpers import _has_artifact, _get_rule_count

def handle_c13(expediente, payload):
    # Registrar Factura MWT (ART-12)
    pass

def handle_c14(expediente, payload):
    # Finalizar Expediente
    # Requirement: check baseline artifacts based on BrandService rules
    # In services.py, this was a complex check
    required_count = _get_rule_count(expediente)
    completed_count = expediente.artifacts.filter(status=ArtifactStatusEnum.COMPLETED).count()
    if completed_count < required_count:
        raise ArtifactMissingError(f"C14 requires {required_count} completed artifacts. Have {completed_count}.")

def handle_c22(expediente, payload):
    # Factura Comisión (ART-10)
    if expediente.mode != 'COMISION':
        raise CommandValidationError("C22 (Issue Commission Invoice) only available in COMISION mode.")
