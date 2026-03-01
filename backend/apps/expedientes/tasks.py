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
    Ref: ENT_OPS_STATE_MACHINE FIX-13, LOTE_SM_SPRINT2 v3.5
    Runs daily via Celery Beat (e.g. 2:00 AM).
    Evaluates all active expedientes where the credit clock has started.
    """
    logger.info("Starting evaluar_relojes_credito task")
    
    # BUG 5: Derive active statuses from enum excluding terminal ones
    terminal_statuses = [ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]
    estados_activos = [s[0] for s in ExpedienteStatus.choices if s[0] not in terminal_statuses]
    
    hoy = timezone.now().date()
    now_time = timezone.now()

    # BUG 3: Move transaction inside loop. BUG 1 & 2: Independent steps for enforcement and events.
    # We fetch IDs first to avoid long-lived transaction across the whole batch
    expediente_ids = Expediente.objects.filter(
        credit_clock_started_at__isnull=False,
        status__in=estados_activos
    ).values_list('expediente_id', flat=True)

    for eid in expediente_ids:
        try:
            with transaction.atomic():
                try:
                    exp = Expediente.objects.select_for_update(skip_locked=True).get(expediente_id=eid)
                except Expediente.DoesNotExist:
                    # Issue 3: Handle skipped due to lock gracefully
                    logger.info(f"Expediente {eid} skipped (locked by another worker)")
                    continue
                
                fecha_inicio = exp.credit_clock_started_at.date()
                dias_transcurridos = (hoy - fecha_inicio).days

                # STEP 1: Enforcement (SIEMPRE si >= 75) - BUG 2
                if dias_transcurridos >= 75 and not exp.is_blocked:
                    logger.info(f"Expediente {exp.expediente_id} reached {dias_transcurridos} days. Blocking via SYSTEM.")
                    # We use service to ensure consistency, but need to pass null user for SYSTEM actor
                    # Note: execute_command will be updated to handle user=None as SYSTEM
                    from .services import execute_command
                    execute_command(
                        exp, 
                        'C17', 
                        {'reason': f"Automated block: {dias_transcurridos} days since credit clock started.", 'actor_type': 'system'}, 
                        user=None
                    )
                
                # STEP 2: Emisión de eventos (Una vez por vida)
                # Spec: credit_clock.warning (60d), credit_clock.critical (75d), credit_clock.expired (90d)
                
                # Critical Event at 75 days (was BLOCKED_POR_MORA)
                if dias_transcurridos >= 75:
                    ya_emitido = EventLog.objects.filter(
                        aggregate_id=exp.expediente_id,
                        event_type='credit_clock.critical'
                    ).exists()

                    if not ya_emitido:
                        logger.info(f"Emitting credit_clock.critical for {exp.expediente_id}")
                        EventLog.objects.create(
                            aggregate_id=exp.expediente_id,
                            aggregate_type=AggregateType.EXPEDIENTE,
                            event_type='credit_clock.critical',
                            emitted_by='SYSTEM:CREDIT_CLOCK',
                            occurred_at=now_time,
                            payload={"dias": dias_transcurridos},
                            correlation_id=uuid.uuid4()
                        )

                # Expired Event at 90 days - Issue 1
                if dias_transcurridos >= 90:
                    ya_expired = EventLog.objects.filter(
                        aggregate_id=exp.expediente_id,
                        event_type='credit_clock.expired'
                    ).exists()

                    if not ya_expired:
                        logger.info(f"Emitting credit_clock.expired for {exp.expediente_id}")
                        EventLog.objects.create(
                            aggregate_id=exp.expediente_id,
                            aggregate_type=AggregateType.EXPEDIENTE,
                            event_type='credit_clock.expired',
                            emitted_by='SYSTEM:CREDIT_CLOCK',
                            occurred_at=now_time,
                            payload={"dias": dias_transcurridos},
                            correlation_id=uuid.uuid4()
                        )

                # Warning Event at 60 days
                if 60 <= dias_transcurridos < 75:
                    ya_notificado = EventLog.objects.filter(
                        aggregate_id=exp.expediente_id,
                        event_type='credit_clock.warning'
                    ).exists()

                    if not ya_notificado:
                        logger.info(f"Expediente {exp.expediente_id} reached {dias_transcurridos} days. Warning.")
                        EventLog.objects.create(
                            aggregate_id=exp.expediente_id,
                            aggregate_type=AggregateType.EXPEDIENTE,
                            event_type='credit_clock.warning',
                            emitted_by='SYSTEM:CREDIT_CLOCK',
                            occurred_at=now_time,
                            payload={"dias": dias_transcurridos},
                            correlation_id=uuid.uuid4()
                        )
        except Exception as e:
            logger.error(f"Error processing expediente {eid}: {str(e)}")
            continue
    
    logger.info("Finished evaluar_relojes_credito task")

from django.utils import timezone

@shared_task
def process_pending_events():
    """ 
    Processes pending EventLogs and marks them as processed.
    Ref: LOTE_SM_SPRINT2 Item 5 — Audit Fix: Added batch limit of 100 and renamed to process_pending_events.
    """
    logger.info("Starting dispatch_events task to process outbox queue")
    
    with transaction.atomic():
        # Select for update to prevent multiple workers processing same events
        # Batch limit of 100 as per Audit Fix
        pending_events = EventLog.objects.select_for_update(skip_locked=True).filter(
            processed_at__isnull=True
        ).order_by('occurred_at')[:100]
        
        for event in pending_events:
            # Simulate processing (e.g. sending to external system)
            logger.info(f"Processing event: {event.event_type} for aggregate {event.aggregate_id}")
            event.processed_at = timezone.now()
            event.save(update_fields=['processed_at'])
            
    logger.info("Finished dispatch_events task")
