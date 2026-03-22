from django.utils import timezone
from django.db import transaction
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


# ─────────────────────────────────────────────────────────────────────
# Sprint 5: Shipment Updates (migrated from services_sprint5.py)
# ─────────────────────────────────────────────────────────────────────

def add_shipment_update(expediente, payload, user):
    """
    S5-08 C36: Add Shipment Update — manual tracking update.
    Appends update entry to ART-05 payload.updates array.
    If ART-05 doesn't exist, creates one with the update.
    """
    import uuid
    from django.utils import timezone

    art05 = ArtifactInstance.objects.filter(
        expediente=expediente,
        artifact_type='ART-05',
        status='completed',
    ).order_by('-created_at').first()

    update_entry = {
        'timestamp': timezone.now().isoformat(),
        'status': payload.get('status', ''),
        'location': payload.get('location', ''),
        'notes': payload.get('notes', ''),
        'source': 'manual',
    }

    with transaction.atomic():
        if art05:
            current_payload = art05.payload or {}
            updates = current_payload.get('updates', [])
            updates.append(update_entry)
            current_payload['updates'] = updates

            if payload.get('tracking_url'):
                current_payload['tracking_url'] = payload['tracking_url']

            art05.payload = current_payload
            art05.save(update_fields=['payload'])
        else:
            art05 = ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type='ART-05',
                payload={
                    'tracking_url': payload.get('tracking_url', ''),
                    'updates': [update_entry],
                },
                status='completed',
            )

        from apps.expedientes.models import EventLog
        EventLog.objects.create(
            event_type='shipment.update_added',
            aggregate_type='expediente',
            aggregate_id=expediente.expediente_id,
            payload={
                'artifact_id': str(art05.artifact_id),
                'update': update_entry,
            },
            occurred_at=timezone.now(),
            emitted_by='C36:AddShipmentUpdate',
            correlation_id=uuid.uuid4(),
        )

    return art05
