import pytest
from apps.expedientes.models import EventLog
from apps.expedientes.tasks import dispatch_events
from apps.expedientes.enums import AggregateType
import uuid
from django.utils import timezone
from .factories import ExpedienteFactory

@pytest.mark.django_db
def test_process_pending_events():
    """Verify that pending events are marked as processed."""
    exp = ExpedienteFactory()
    
    # Create some events
    EventLog.objects.create(
        aggregate_id=exp.expediente_id,
        aggregate_type=AggregateType.EXPEDIENTE,
        event_type='TEST_EVENT_1',
        payload={},
        emitted_by='TEST',
        occurred_at=timezone.now(),
        correlation_id=uuid.uuid4()
    )
    EventLog.objects.create(
        aggregate_id=exp.expediente_id,
        aggregate_type=AggregateType.EXPEDIENTE,
        event_type='TEST_EVENT_2',
        payload={},
        emitted_by='TEST',
        occurred_at=timezone.now(),
        correlation_id=uuid.uuid4()
    )
    
    # Run task
    dispatch_events()
    
    assert EventLog.objects.filter(processed_at__isnull=False).count() == 2

@pytest.mark.django_db
def test_process_pending_events_limit():
    """Verify processing limit (100)."""
    exp = ExpedienteFactory()
    
    # Create 150 events
    events = []
    for i in range(150):
        events.append(EventLog(
            aggregate_id=exp.expediente_id,
            aggregate_type=AggregateType.EXPEDIENTE,
            event_type=f'TEST_EVENT_{i}',
            payload={},
            emitted_by='TEST',
            occurred_at=timezone.now(),
            correlation_id=uuid.uuid4()
        ))
    EventLog.objects.bulk_create(events)
    
    # Run task
    dispatch_events()
    
    assert EventLog.objects.filter(processed_at__isnull=False).count() == 100
    assert EventLog.objects.filter(processed_at__isnull=True).count() == 50
