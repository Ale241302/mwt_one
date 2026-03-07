import pytest
from django.utils import timezone
from datetime import timedelta
from apps.expedientes.models import Expediente, EventLog
from apps.expedientes.enums import ExpedienteStatus, BlockedByType
from apps.expedientes.tasks import evaluar_relojes_credito
from .factories import LegalEntityFactory, ExpedienteFactory

@pytest.mark.django_db
def test_credit_clock_60_days_warning():
    """Verify warning event at 60 days."""
    exp = ExpedienteFactory(
        status=ExpedienteStatus.PRODUCCION,
        credit_clock_started_at=timezone.now() - timedelta(days=61)
    )
    
    evaluar_relojes_credito()
    
    # Check event
    assert EventLog.objects.filter(
        aggregate_id=exp.expediente_id,
        event_type='WARNING_60_DIAS'
    ).exists()

@pytest.mark.django_db
def test_credit_clock_75_days_blocking():
    """Verify automatic block at 75 days (Audit Fix)."""
    exp = ExpedienteFactory(
        status=ExpedienteStatus.DESPACHO,
        credit_clock_started_at=timezone.now() - timedelta(days=76)
    )
    
    evaluar_relojes_credito()
    
    exp.refresh_from_db()
    assert exp.is_blocked is True
    assert exp.blocked_by_type == BlockedByType.SYSTEM
    assert exp.blocked_by_id == "CREDIT_CLOCK_MONITOR"
    
    # Check event
    assert EventLog.objects.filter(
        aggregate_id=exp.expediente_id,
        event_type='BLOCKED_POR_MORA'
    ).exists()

@pytest.mark.django_db
def test_credit_clock_concurrency_skip_locked():
    """Verify that skip_locked works when an expediente is already locked."""
    from django.db import transaction
    
    exp = ExpedienteFactory(
        status=ExpedienteStatus.PRODUCCION,
        credit_clock_started_at=timezone.now() - timedelta(days=80)
    )
    
    # Lock the expediente in a separate transaction (manually)
    with transaction.atomic():
        Expediente.objects.select_for_update().get(pk=exp.pk)
        
        # This call should skip the locked record and not block it (since skip_locked=True)
        evaluar_relojes_credito()
        
    exp.refresh_from_db()
    # Since it was skipped, it shouldn't have been blocked by the task
    assert exp.is_blocked is False

@pytest.mark.django_db
def test_credit_clock_idempotency():
    """Verify events are not duplicated."""
    exp = ExpedienteFactory(
        status=ExpedienteStatus.PRODUCCION,
        credit_clock_started_at=timezone.now() - timedelta(days=65)
    )
    
    # Run twice
    evaluar_relojes_credito()
    evaluar_relojes_credito()
    
    count = EventLog.objects.filter(
        aggregate_id=exp.expediente_id,
        event_type='WARNING_60_DIAS'
    ).count()
    assert count == 1

@pytest.mark.django_db
def test_credit_clock_ignored_terminal_status():
    """Verify terminal statuses are ignored."""
    exp = ExpedienteFactory(
        status=ExpedienteStatus.CERRADO,
        credit_clock_started_at=timezone.now() - timedelta(days=100)
    )
    
    evaluar_relojes_credito()
    
    exp.refresh_from_db()
    assert exp.is_blocked is False
    assert not EventLog.objects.filter(aggregate_id=exp.expediente_id).exists()
