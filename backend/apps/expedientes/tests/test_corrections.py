import pytest
from apps.expedientes.models import ArtifactInstance, EventLog
from apps.expedientes.enums import ExpedienteStatus, ArtifactStatus
from apps.expedientes.services import supersede_artifact, void_artifact, execute_command
from .factories import ExpedienteFactory, ArtifactInstanceFactory, UserFactory

@pytest.mark.django_db
def test_supersede_artifact_happy_path():
    user = UserFactory(is_superuser=True)
    exp = ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
    art = ArtifactInstanceFactory(
        expediente=exp,
        artifact_type='ART-01',
        status=ArtifactStatus.COMPLETED,
        payload={'data': 'old'}
    )
    
    new_payload = {'data': 'new'}
    exp, new_art, event = supersede_artifact(art.artifact_id, new_payload, user)
    
    art.refresh_from_db()
    assert art.status == ArtifactStatus.SUPERSEDED
    assert art.superseded_by == new_art
    assert new_art.payload == new_payload
    assert event.event_type == 'artifact.superseded'

@pytest.mark.django_db
def test_supersede_artifact_triggers_block():
    """Verify blocking if corrected downstream."""
    user = UserFactory(is_superuser=True)
    # ART-01 is created in REGISTRO. If we are in PRODUCCION, it should block.
    exp = ExpedienteFactory(status=ExpedienteStatus.PRODUCCION)
    art = ArtifactInstanceFactory(
        expediente=exp,
        artifact_type='ART-01',
        status=ArtifactStatus.COMPLETED
    )
    
    exp, new_art, event = supersede_artifact(art.artifact_id, {}, user)
    
    exp.refresh_from_db()
    assert exp.is_blocked is True
    assert exp.blocked_by_id == 'ARTIFACT_CORRECTION'
    
    # Check block event
    assert EventLog.objects.filter(
        aggregate_id=exp.expediente_id,
        event_type='BLOCKED_POR_CAMBIO_PRECONDICION'
    ).exists()

@pytest.mark.django_db
def test_void_artifact_art09_only():
    user = UserFactory(is_superuser=True)
    exp = ExpedienteFactory(status=ExpedienteStatus.EN_DESTINO)
    
    # 1. Try to void ART-01 (should fail)
    art01 = ArtifactInstanceFactory(expediente=exp, artifact_type='ART-01', status=ArtifactStatus.COMPLETED)
    with pytest.raises(Exception): # CommandValidationError
        void_artifact(art01.artifact_id, user)
        
    # 2. Void ART-09 (should work)
    art09 = ArtifactInstanceFactory(expediente=exp, artifact_type='ART-09', status=ArtifactStatus.COMPLETED)
    exp, voided_art, event = void_artifact(art09.artifact_id, user)
    
    assert voided_art.status == ArtifactStatus.VOID
    assert event.event_type == 'artifact.voided'

@pytest.mark.django_db
def test_void_artifact_triggers_block():
    user = UserFactory(is_superuser=True)
    # ART-09 created in EN_DESTINO. If CERRADO, block.
    # Note: Terminal states check happens before block check.
    # Actually, if CERRADO, it should raise error.
    exp = ExpedienteFactory(status=ExpedienteStatus.CERRADO)
    art = ArtifactInstanceFactory(expediente=exp, artifact_type='ART-09', status=ArtifactStatus.COMPLETED)
    
    with pytest.raises(Exception): # Terminal state check
        void_artifact(art.artifact_id, user)

@pytest.mark.django_db
def test_artifact_correction_terminal_state_denied():
    user = UserFactory(is_superuser=True)
    exp = ExpedienteFactory(status=ExpedienteStatus.CANCELADO)
    art = ArtifactInstanceFactory(expediente=exp, artifact_type='ART-01', status=ArtifactStatus.COMPLETED)
    
    with pytest.raises(Exception):
        supersede_artifact(art.artifact_id, {}, user)
