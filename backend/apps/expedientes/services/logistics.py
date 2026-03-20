from django.utils import timezone
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.models import ArtifactInstance
from apps.expedientes.exceptions import CommandValidationError, ArtifactMissingError

def handle_c23(expediente, payload):
    # Agregar Opción Logística (ART-19)
    # Check if ART-19 already exists and is pending
    art19 = expediente.artifacts.filter(artifact_type='ART-19', status='pending').first()
    if not art19:
        art19 = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type='ART-19',
            status='pending',
            payload={'options': []}
        )
    
    options = art19.payload.get('options', [])
    new_option = {
        'id': len(options) + 1,
        'provider': payload.get('provider'),
        'cost': payload.get('cost'),
        'eta': payload.get('eta'),
        'notes': payload.get('notes'),
        'created_at': str(timezone.now()) if 'timezone' in globals() else None
    }
    options.append(new_option)
    art19.payload['options'] = options
    art19.save(update_fields=['payload'])

def handle_c24(expediente, payload):
    # Decidir Logística (ART-19)
    art19 = expediente.artifacts.filter(artifact_type='ART-19', status='pending').first()
    if not art19:
        raise ArtifactMissingError("C24 requires a pending ART-19.")
    
    option_id = payload.get('option_id')
    art19.payload['selected_option_id'] = option_id
    art19.status = ArtifactStatusEnum.COMPLETED
    art19.save(update_fields=['payload', 'status'])

def handle_c30(expediente, payload):
    # Materializar Logística (C30)
    # This usually creates ART-11 (Arribo) or similar?
    # In services.py it was just a mock logic for now
    pass
