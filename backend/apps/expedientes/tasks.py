from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging
import uuid

from .models import Expediente, EventLog
from .enums import ExpedienteStatus, AggregateType, BlockedByType

logger = logging.getLogger(__name__)

@shared_task
def evaluar_relojes_credito():
    """
    Ref: ENT_OPS_STATE_MACHINE FIX-13
    Runs daily via Celery Beat (e.g. 2:00 AM).
    Evaluates all active expedientes where the credit clock has started.
    """
    logger.info("Starting evaluar_relojes_credito task")
    
    estados_activos = [
        ExpedienteStatus.PRODUCCION,
        ExpedienteStatus.PREPARACION,
        ExpedienteStatus.DESPACHO
    ]
    
    hoy = timezone.now().date()
    now_time = timezone.now()

    # Wrap in transaction for select_for_update
    with transaction.atomic():
        # Lock active expedientes with started credit clocks
        expedientes = Expediente.objects.select_for_update(skip_locked=True).filter(
            credit_clock_started_at__isnull=False,
            status__in=estados_activos,
            is_blocked=False # Don't process already blocked
        )

        for exp in expedientes:
            fecha_inicio = exp.credit_clock_started_at.date()
            dias_transcurridos = (hoy - fecha_inicio).days

            # 1. Block at 90 days
            if dias_transcurridos >= 90:
                ya_bloqueado = EventLog.objects.filter(
                    aggregate_id=exp.expediente_id,
                    event_type='BLOCKED_POR_MORA'
                ).exists()

                if not ya_bloqueado:
                    logger.info(f"Expediente {exp.expediente_id} reached 90 days. Blocking.")
                    
                    # Block expediente
                    exp.is_blocked = True
                    exp.blocked_reason = f"Automated block: {dias_transcurridos} days since credit clock started."
                    exp.blocked_at = now_time
                    exp.blocked_by_type = BlockedByType.SYSTEM
                    exp.blocked_by_id = "CREDIT_CLOCK_MONITOR"
                    exp.save(update_fields=['is_blocked', 'blocked_reason', 'blocked_at', 'blocked_by_type', 'blocked_by_id'])
                    
                    # Dispatch event
                    EventLog.objects.create(
                        aggregate_id=exp.expediente_id,
                        aggregate_type=AggregateType.EXPEDIENTE,
                        event_type='BLOCKED_POR_MORA',
                        emitted_by='SYSTEM:CREDIT_CLOCK',
                        occurred_at=now_time,
                        payload={"dias": dias_transcurridos},
                        correlation_id=uuid.uuid4()
                    )

            # 2. Warning at 75 days
            elif 75 <= dias_transcurridos < 90:
                ya_notificado = EventLog.objects.filter(
                    aggregate_id=exp.expediente_id,
                    event_type='WARNING_75_DIAS'
                ).exists()

                if not ya_notificado:
                    logger.info(f"Expediente {exp.expediente_id} reached 75 days. Warning.")
                    EventLog.objects.create(
                        aggregate_id=exp.expediente_id,
                        aggregate_type=AggregateType.EXPEDIENTE,
                        event_type='WARNING_75_DIAS',
                        emitted_by='SYSTEM:CREDIT_CLOCK',
                        occurred_at=now_time,
                        payload={"dias": dias_transcurridos},
                        correlation_id=uuid.uuid4()
                    )

            # 3. Warning at 60 days
            elif 60 <= dias_transcurridos < 75:
                ya_notificado = EventLog.objects.filter(
                    aggregate_id=exp.expediente_id,
                    event_type='WARNING_60_DIAS'
                ).exists()

                if not ya_notificado:
                    logger.info(f"Expediente {exp.expediente_id} reached 60 days. Warning.")
                    EventLog.objects.create(
                        aggregate_id=exp.expediente_id,
                        aggregate_type=AggregateType.EXPEDIENTE,
                        event_type='WARNING_60_DIAS',
                        emitted_by='SYSTEM:CREDIT_CLOCK',
                        occurred_at=now_time,
                        payload={"dias": dias_transcurridos},
                        correlation_id=uuid.uuid4()
                    )
    
    logger.info("Finished evaluar_relojes_credito task")

from django.utils import timezone

@shared_task
def dispatch_events():
    """ Processes pending EventLogs and marks them as processed. """
    logger.info("Starting dispatch_events task to process outbox queue")
    pending_events = EventLog.objects.filter(processed_at__isnull=True).order_by('occurred_at')
    
    with transaction.atomic():
        for event in pending_events:
            # Simulate processing (e.g. sending to external system)
            logger.info(f"Processing event: {event.event_type} for aggregate {event.aggregate_id}")
            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])
            
    logger.info("Finished dispatch_events task")
