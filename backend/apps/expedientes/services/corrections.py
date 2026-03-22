import uuid
from django.utils import timezone
from django.db import transaction
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.models import ArtifactInstance, EventLog

def supersede_artifact(artifact_id, new_payload, user):
    from django.apps import apps
    ArtifactInstance = apps.get_model('expedientes', 'ArtifactInstance')
    EventLog = apps.get_model('expedientes', 'EventLog')
    
    if not artifact_id:
        raise ValueError("artifact_id is required")

    with transaction.atomic():
        try:
            old_art = ArtifactInstance.objects.select_for_update().get(pk=artifact_id)
            exp = old_art.expediente
            
            # Validation: Terminal States
            if exp.status in [ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]:
                raise Exception(f"Cannot correct artifact in terminal state {exp.status}")
                
            # Validation: Only COMPLETED artifacts can be superseded
            if old_art.status != ArtifactStatusEnum.COMPLETED:
                raise Exception(f"Only COMPLETED artifacts can be superseded. Current: {old_art.status}")
            
            # 1. Create new artifact
            new_art = ArtifactInstance.objects.create(
                expediente=exp,
                artifact_type=old_art.artifact_type,
                status=ArtifactStatusEnum.COMPLETED,
                payload=new_payload
            )
            
            # 2. Update old artifact
            old_art.status = ArtifactStatusEnum.SUPERSEDED
            old_art.superseded_by = new_art
            old_art.save()
            
            # 3. Block logic
            # Business Rule: If an artifact is superseded in PRODUCCION or later, block
            # For this MVP, we consider everything after REGISTRO as "later"
            if exp.status != ExpedienteStatus.REGISTRO:
                exp.is_blocked = True
                exp.blocked_by_id = 'ARTIFACT_CORRECTION'
                exp.save()
                
                EventLog.objects.create(
                    event_type='BLOCKED_POR_CAMBIO_PRECONDICION',
                    aggregate_type='expediente',
                    aggregate_id=exp.expediente_id,
                    payload={'reason': 'Artifact superseded downstream', 'artifact_id': str(old_art.pk)},
                    occurred_at=timezone.now(),
                    emitted_by='SYSTEM',
                    correlation_id=uuid.uuid4()
                )
            
            # 4. Log correction event
            event = EventLog.objects.create(
                event_type='artifact.superseded',
                aggregate_type='expediente',
                aggregate_id=exp.expediente_id,
                payload={
                    'old_id': str(old_art.pk),
                    'new_id': str(new_art.pk)
                },
                occurred_at=timezone.now(),
                emitted_by=str(user.username if hasattr(user, 'username') else user),
                correlation_id=uuid.uuid4()
            )
            return exp, new_art, event
        except ArtifactInstance.DoesNotExist:
            raise Exception("Artifact not found")

def void_artifact(artifact_id, user):
    from django.apps import apps
    ArtifactInstance = apps.get_model('expedientes', 'ArtifactInstance')
    EventLog = apps.get_model('expedientes', 'EventLog')

    with transaction.atomic():
        try:
            art = ArtifactInstance.objects.select_for_update().get(pk=artifact_id)
            exp = art.expediente
            
            # Validation: Terminal States
            if exp.status in [ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]:
                raise Exception(f"Cannot correct artifact in terminal state {exp.status}")
            
            # Validation: Only ART-09 can be voided
            if art.artifact_type != 'ART-09':
                raise Exception("Only ART-09 (Logistics Option Selection) can be voided.")
            
            # 1. Update status
            art.status = ArtifactStatusEnum.VOID
            art.save()
            
            # 2. Block logic (voiding also triggers block if downstream)
            if exp.status != ExpedienteStatus.REGISTRO:
                 exp.is_blocked = True
                 exp.blocked_by_id = 'ARTIFACT_CORRECTION'
                 exp.save()
                 
                 EventLog.objects.create(
                    event_type='BLOCKED_POR_CAMBIO_PRECONDICION',
                    aggregate_type='expediente',
                    aggregate_id=exp.expediente_id,
                    payload={'reason': 'Artifact voided downstream', 'artifact_id': str(art.pk)},
                    occurred_at=timezone.now(),
                    emitted_by='SYSTEM',
                    correlation_id=uuid.uuid4()
                )
            
            # 3. Log event
            event = EventLog.objects.create(
                event_type='artifact.voided',
                aggregate_type='expediente',
                aggregate_id=exp.expediente_id,
                payload={'voided_id': str(art.pk)},
                occurred_at=timezone.now(),
                emitted_by=str(user.username if hasattr(user, 'username') else user),
                correlation_id=uuid.uuid4()
            )
            return exp, art, event
        except ArtifactInstance.DoesNotExist:
            raise Exception("Artifact not found")

def handle_c19(expediente, payload):
    """Entry point for C19: Supersede Artifact."""
    pass

def handle_c20(expediente, payload):
    """Entry point for C20: Void Artifact."""
    pass


# ─────────────────────────────────────────────────────────────────────
# Sprint 5: Compensation (migrated from services_sprint5.py)
# ─────────────────────────────────────────────────────────────────────

def register_compensation(expediente, payload, user):
    """
    S5-05 C29: RegisterCompensation — CEO-only.
    Creates ArtifactInstance type ART-12.
    Voidable via C20 (VoidArtifact).
    """
    if not user.is_superuser:
        raise PermissionError("Only CEO can register compensation notes.")

    with transaction.atomic():
        artifact = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type='ART-12',
            payload={
                'amount': str(payload.get('amount', 0)),
                'currency': payload.get('currency', 'USD'),
                'reason': payload.get('reason', ''),
                'beneficiary': payload.get('beneficiary', ''),
                'reference': payload.get('reference', ''),
                'notes': payload.get('notes', ''),
            },
            status='completed',
        )

        EventLog.objects.create(
            event_type='compensation.registered',
            aggregate_type='expediente',
            aggregate_id=expediente.expediente_id,
            payload={
                'artifact_id': str(artifact.artifact_id),
                'amount': str(payload.get('amount', 0)),
            },
            occurred_at=timezone.now(),
            emitted_by='C29:RegisterCompensation',
            correlation_id=uuid.uuid4(),
        )

    return artifact
