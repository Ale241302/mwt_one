"""S17-02: Handler for DESPACHO → TRANSITO transition (C11B)."""
from django.utils import timezone
from apps.expedientes.models import EventLog
import uuid


def handle_c11b(expediente, payload):
    """
    S17-02: Confirms departure from DESPACHO state, transitioning to TRANSITO.
    Called by dispatcher when command C11B is executed.
    The actual status transition is managed by the dispatcher (execute_command).
    This handler records any dispatch-specific event data.
    """
    dispatch_info = payload.get('dispatch_info', {})

    EventLog.objects.create(
        event_type='command.C11B.despacho_a_transito',
        aggregate_type='expediente',
        aggregate_id=expediente.expediente_id,
        payload={
            'command': 'C11B',
            'dispatch_info': dispatch_info,
            'expediente_id': str(expediente.expediente_id),
        },
        occurred_at=timezone.now(),
        emitted_by='C11B',
        correlation_id=uuid.uuid4()
    )
    return expediente
