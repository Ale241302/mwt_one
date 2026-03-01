import pytest
from apps.expedientes.models import EventLog
from apps.expedientes.tasks import process_pending_events
from .factories import ExpedienteFactory

@pytest.mark.django_db
def test_process_pending_events():
    """Verify that pending events are marked as processed."""
    exp = ExpedienteFactory()
    
    # Create some events
    EventLog.objects.create(
        aggregate_id=exp.expediente_id,
        event_type='TEST_EVENT_1',
        payload={},
        actor_id='TEST'
    )
    EventLog.objects.create(
        aggregate_id=exp.expediente_id,
        event_type='TEST_EVENT_2',
        payload={},
        actor_id='TEST'
    )
    
    # Run task
    processed_count = process_pending_events()
    
    assert processed_count == 2
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
            event_type=f'TEST_EVENT_{i}',
            payload={},
            actor_id='TEST'
        ))
    EventLog.objects.bulk_create(events)
    
    # Run task
    processed_count = process_pending_events()
    
    assert processed_count == 100
    assert EventLog.objects.filter(processed_at__isnull=False).count() == 100
    assert EventLog.objects.filter(processed_at__isnull=True).count() == 50
