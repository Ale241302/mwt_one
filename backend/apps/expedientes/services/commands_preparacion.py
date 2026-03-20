from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import ArtifactMissingError
from .helpers import _has_artifact

def handle_c7(expediente, payload):
    # Cargar Packing List (ART-06)
    pass

def handle_c8(expediente, payload):
    # Cargar Factura Comercial (ART-07)
    pass

def handle_c9(expediente, payload):
    # Cargar Certificado de Origen (ART-08)
    pass

def handle_c10(expediente, payload):
    # Cargar Otros Documentos (ART-13)
    pass

def handle_c11(expediente, payload):
    # Confirmar Salida Aduana (China)
    # Requirement: ART-06 (Packing List) & ART-07 (Factura Comercial)
    if not _has_artifact(expediente, 'ART-06'):
        raise ArtifactMissingError("C11 requires ART-06 (Packing List).")
    if not _has_artifact(expediente, 'ART-07'):
        raise ArtifactMissingError("C11 requires ART-07 (Commercial Invoice).")
