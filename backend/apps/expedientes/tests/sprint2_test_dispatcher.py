import pytest
import datetime
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.expedientes.models import EventLog
from apps.expedientes.tasks import dispatch_events

@pytest.mark.django_db
def test_dispatcher_processes_pending_events():
    # Create some pending events
    event1 = EventLog.objects.create(
        event_type="test.event1", aggregate_type="expediente", aggregate_id="00000000-0000-0000-0000-000000000000",
        occurred_at=timezone.now(), emitted_by="test", correlation_id="11111111-1111-1111-1111-111111111111"
    )
    event2 = EventLog.objects.create(
        event_type="test.event2", aggregate_type="expediente", aggregate_id="00000000-0000-0000-0000-000000000000",
        occurred_at=timezone.now(), emitted_by="test", correlation_id="22222222-2222-2222-2222-222222222222"
    )
    
    assert EventLog.objects.filter(processed_at__isnull=True).count() == 2
    
    # Run the dispatcher
    dispatch_events()
    
    assert EventLog.objects.filter(processed_at__isnull=True).count() == 0
    event1.refresh_from_db()
    event2.refresh_from_db()
    assert event1.processed_at is not None
    assert event2.processed_at is not None

@pytest.mark.django_db
def test_dispatcher_ignores_processed_events():
    # Create already processed event
    event1 = EventLog.objects.create(
        event_type="test.event1", aggregate_type="expediente", aggregate_id="00000000-0000-0000-0000-000000000000",
        occurred_at=timezone.now(), emitted_by="test", correlation_id="11111111-1111-1111-1111-111111111111",
        processed_at=timezone.now()
    )
    original_processed_at = event1.processed_at
    
    # Run dispatcher
    dispatch_events()
    
    event1.refresh_from_db()
    assert event1.processed_at == original_processed_at

@pytest.mark.django_db
def test_dispatcher_is_idempotent():
    event1 = EventLog.objects.create(
        event_type="test.event1", aggregate_type="expediente", aggregate_id="00000000-0000-0000-0000-000000000000",
        occurred_at=timezone.now(), emitted_by="test", correlation_id="11111111-1111-1111-1111-111111111111"
    )
    
    # Run once
    dispatch_events()
    event1.refresh_from_db()
    processed_at_1 = event1.processed_at
    assert processed_at_1 is not None
    
    # Run again should not change it
    dispatch_events()
    event1.refresh_from_db()
    assert event1.processed_at == processed_at_1
