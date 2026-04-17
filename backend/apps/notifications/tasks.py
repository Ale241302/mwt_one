"""
S26-05: send_notification — Custom Celery Task con on_failure().
S26-07: check_overdue_payments — Cron diario cobranza.

Arquitectura:
- SendNotificationTask: clase custom con on_failure() para Log(exhausted) cuando retries se agotan.
- autoretry_for=(RetryableEmailError,) — Celery maneja retries automáticamente.
- advisory lock via pg_advisory_xact_lock con sha256 determinístico.
- Send FUERA de transaction. Lock+check+log DENTRO de transaction.
- Semántica: AT-LEAST-ONCE entrega. Persistencia deduplicada.
"""
import hashlib
import logging
import struct
import uuid as uuid_module

from celery import shared_task, Task
from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from datetime import timedelta

from apps.notifications.backends import SendResult, get_email_backend
from apps.notifications.services import (
    resolve_notification_recipient,
    resolve_collection_recipient,
    resolve_template,
    build_notification_context,
)
from apps.notifications.models import (
    NotificationAttempt, NotificationLog, CollectionEmailLog,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Helpers — advisory lock + sha256 key
# =============================================================================

def _stable_lock_key(value: str) -> int:
    """sha256-based lock key — determinístico across workers. No Python hash()."""
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return struct.unpack("<q", digest[:8])[0]


def _advisory_lock_for_event(event_log_id, recipient_email: str):
    """Adquiere pg_advisory_xact_lock. Debe llamarse dentro de transaction.atomic()."""
    lock_key = _stable_lock_key(f"notif:{event_log_id}:{recipient_email}")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])


# =============================================================================
# Exceptions
# =============================================================================

class RetryableEmailError(Exception):
    """Raised when backend returns RETRYABLE. Celery retries via autoretry_for."""
    pass


# =============================================================================
# Terminal log helpers — single point of truth
# =============================================================================

def _create_terminal(log_base: dict, status: str, subject: str, body_preview: str,
                     template=None, error: str = '', attempt_count: int = 1):
    """Crea NotificationLog con completed_at. Single point of terminal log creation."""
    NotificationLog.objects.create(
        **log_base,
        status=status,
        subject=subject,
        body_preview=body_preview[:500],
        template=template,
        error=error,
        completed_at=timezone.now(),
        attempt_count=attempt_count,
    )


def _persist_terminal(event_log_id, recipient: str, log_base: dict, status: str,
                      subject: str, body_preview: str, template=None,
                      error: str = '', attempt_count: int = 1):
    """Persiste NotificationLog con advisory lock si event-triggered, o directamente si manual."""
    if event_log_id:
        with transaction.atomic():
            _advisory_lock_for_event(event_log_id, recipient)
            if NotificationLog.objects.filter(
                event_log_id=event_log_id, recipient_email=recipient
            ).exists():
                return
            _create_terminal(log_base, status, subject, body_preview,
                              template=template, error=error, attempt_count=attempt_count)
    else:
        _create_terminal(log_base, status, subject, body_preview,
                         template=template, error=error, attempt_count=attempt_count)


# =============================================================================
# S26-05: SendNotificationTask — Custom Task con on_failure()
# =============================================================================

class SendNotificationTask(Task):
    """
    Custom Task con on_failure() callback (fix B1 R13).
    Cuando todos los retries se agotan, on_failure() persiste Log(exhausted).
    Patrón canónico Celery — no necesita MaxRetriesExceededError inline.
    """
    max_retries = 3
    default_retry_delay = 60

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Llamado por Celery después de que todos los retries se agotan."""
        event_log_id = kwargs.get('event_log_id')
        expediente_id = kwargs.get('expediente_id')
        template_key = kwargs.get('template_key', '')
        trigger_action_source = kwargs.get('trigger_action_source', '')
        proforma_id = kwargs.get('proforma_id')
        recipient = kwargs.get('_recipient', 'N/A')
        correlation_id_str = kwargs.get('_correlation_id')

        if not correlation_id_str:
            logger.error(f"[NOTIF_FAILURE] on_failure called without _correlation_id — task_id={task_id}")
            return

        try:
            expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
            expediente = expediente_model.objects.get(pk=expediente_id)
        except Exception:
            return

        try:
            correlation_id = uuid_module.UUID(correlation_id_str) if isinstance(correlation_id_str, str) else correlation_id_str
            log_base = {
                'correlation_id': correlation_id,
                'event_log_id': event_log_id,
                'expediente_id': expediente_id,
                'proforma_id': proforma_id,
                'recipient_email': recipient,
                'template_key': template_key,
                'trigger_action_source': trigger_action_source,
            }
            act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
            _persist_terminal(
                event_log_id, recipient, log_base, 'exhausted',
                'N/A', f'All retries exhausted: {str(exc)[:400]}',
                error=f'Exhausted after {act} attempts: {str(exc)[:300]}',
                attempt_count=act or 1,
            )
        except Exception as inner_exc:
            logger.error(f"[NOTIF_FAILURE] on_failure cleanup failed: {inner_exc}")


@shared_task(
    bind=True,
    base=SendNotificationTask,
    autoretry_for=(RetryableEmailError,),
    retry_kwargs={'max_retries': 3},
    default_retry_delay=60,
    name='apps.notifications.tasks.send_notification',
)
def send_notification(
    self,
    template_key: str,
    expediente_id: str,
    proforma_id: str = None,
    event_log_id: str = None,
    trigger_action_source: str = '',
    extra_context: dict = None,
    _recipient: str = None,
    _correlation_id: str = None,
):
    """
    Task principal de notificación email transaccional.
    Flujo: kill-switch → dedup → resolve → render → send → log terminal.
    """
    try:
        expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
        expediente = expediente_model.objects.select_related(
            'brand', 'client'
        ).get(pk=expediente_id)
    except Exception:
        logger.warning(f"[NOTIF] Expediente not found: {expediente_id}")
        return

    try:
        from apps.clientes.models import ClientSubsidiary
        subsidiary = ClientSubsidiary.objects.filter(
            legal_entity=expediente.client, is_active=True
        ).first()
        language = (getattr(subsidiary, 'preferred_language', None) or 'es') if subsidiary else 'es'
    except Exception:
        language = 'es'

    brand = expediente.brand

    # --- correlation_id: generado una vez, guardado en kwargs para on_failure ---
    if not _correlation_id:
        correlation_id = uuid_module.UUID(str(event_log_id)) if event_log_id else uuid_module.uuid4()
        # Stash para on_failure
        self.request.kwargs['_correlation_id'] = str(correlation_id)
        _correlation_id = str(correlation_id)
    else:
        correlation_id = uuid_module.UUID(_correlation_id) if isinstance(_correlation_id, str) else _correlation_id

    recipient = _recipient or resolve_notification_recipient(expediente, proforma_id)
    if not _recipient:
        self.request.kwargs['_recipient'] = recipient or 'N/A'

    attempt_base = {
        'correlation_id': correlation_id,
        'event_log_id': event_log_id,
        'expediente_id': expediente_id,
        'proforma_id': proforma_id,
        'recipient_email': recipient or 'N/A',
        'template_key': template_key,
        'trigger_action_source': trigger_action_source,
    }
    log_base = {
        'correlation_id': correlation_id,
        'event_log_id': event_log_id,
        'expediente_id': expediente_id,
        'proforma_id': proforma_id,
        'recipient_email': recipient or 'N/A',
        'template_key': template_key,
        'trigger_action_source': trigger_action_source,
    }

    # --- Kill switch ---
    if not getattr(settings, 'MWT_NOTIFICATION_ENABLED', False):
        if event_log_id:
            with transaction.atomic():
                _advisory_lock_for_event(event_log_id, recipient or 'N/A')
                if not NotificationLog.objects.filter(
                    event_log_id=event_log_id,
                    recipient_email=recipient or 'N/A'
                ).exists():
                    _create_terminal(log_base, 'disabled', '[DISABLED]',
                                     f'Kill switch off. template_key={template_key}')
        else:
            _create_terminal(log_base, 'disabled', '[DISABLED]',
                             f'Kill switch off. template_key={template_key}')
        NotificationAttempt.objects.create(**attempt_base, status='disabled')
        return

    # --- Dedup check (solo event-triggered) ---
    if event_log_id:
        already_terminal = NotificationLog.objects.filter(
            event_log_id=event_log_id,
            recipient_email=recipient or 'N/A',
        ).exists()
        if already_terminal:
            return

    # --- Resolve template ---
    template = resolve_template(template_key, brand, language)
    if not template:
        NotificationAttempt.objects.create(**attempt_base, status='skipped', error='Template not found')
        _persist_terminal(event_log_id, recipient or 'N/A', log_base, 'skipped',
                          'N/A', f'Template not found: {template_key}')
        return

    # --- Validate recipient ---
    if not recipient or recipient == 'N/A':
        NotificationAttempt.objects.create(**attempt_base, status='skipped', error='No contact_email')
        _persist_terminal(event_log_id, 'N/A', log_base, 'skipped',
                          'N/A', 'No contact_email configured')
        return

    # --- Render Jinja2 (try/except — creates audit trail on error) ---
    try:
        from jinja2.sandbox import SandboxedEnvironment
        context = build_notification_context(expediente, proforma_id, extra_context)
        env = SandboxedEnvironment()
        subject = env.from_string(template.subject_template).render(context)
        body = env.from_string(template.body_template).render(context)
    except Exception as exc:
        render_error = f'Render error: {str(exc)[:400]}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=render_error)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          'N/A', render_error, template=template,
                          error=render_error, attempt_count=act)
        return

    # --- Send (FUERA de transaction) — SendResult branching ---
    backend = get_email_backend()
    try:
        send_result = backend.send(to=recipient, subject=subject, body=body)
    except Exception as exc:
        # Fix B1 R12: excepción no mapeada del backend — crear audit trail antes de salir
        error_msg = f'Backend exception: {str(exc)[:400]}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=error_msg)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          subject, body[:500], template=template,
                          error=error_msg, attempt_count=act)
        return

    if send_result is SendResult.RETRYABLE:
        # Fix B1 R13: log attempt, raise RetryableEmailError.
        # Celery retries, cuando se agotan → on_failure() persiste Log(exhausted).
        NotificationAttempt.objects.create(**attempt_base, status='failed', error='Retryable failure')
        raise RetryableEmailError('Retryable email failure')

    elif send_result is SendResult.PERMANENT:
        NotificationAttempt.objects.create(**attempt_base, status='failed', error='Permanent failure')
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          subject, body[:500], template=template,
                          error='Permanent email failure', attempt_count=act)
        return

    elif send_result is SendResult.SENT:
        NotificationAttempt.objects.create(**attempt_base, status='sent')
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'sent',
                          subject, body[:500], template=template, attempt_count=act)

    else:
        # Fix M2 R13: Unknown SendResult → audit trail, no RuntimeError
        error_msg = f'Unknown SendResult: {send_result}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=error_msg)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          subject, body[:500], template=template,
                          error=error_msg, attempt_count=act)
        return


# =============================================================================
# S26-07: check_overdue_payments — Cron diario cobranza
# =============================================================================

@shared_task(name='apps.notifications.tasks.check_overdue_payments')
def check_overdue_payments():
    """
    Cron diario: 8:00 AM Costa Rica (14:00 UTC).
    Kill switch: solo logger.info, NO crea CollectionEmailLog.
    """
    if not getattr(settings, 'MWT_NOTIFICATION_ENABLED', False):
        logger.info("[COLLECTION_DISABLED] MWT_NOTIFICATION_ENABLED=False — no action taken")
        return

    payment_model = ModuleRegistry.get_model('finance', 'Payment')
    if not payment_model:
        logger.error("[COLLECTION_ERROR] Finance module not found")
        return

    today = timezone.now().date()

    # S25/S26 Status Mapping: pending, partial, verified
    qs = payment_model.objects.filter(
        status__in=['pending', 'partial', 'verified'],
    )

    for pago in qs:
        # Revalidar estado
        pago.refresh_from_db(fields=['status'])
        if pago.status not in ['pending', 'partial', 'verified']:
            continue

        expediente = pago.expediente # Property resolve_ref
        if not expediente:
            continue

        # Días de gracia
        try:
            from apps.clientes.models import ClientSubsidiary
            subsidiary = ClientSubsidiary.objects.filter(
                legal_entity=expediente.client, # client is property resolve_ref
                is_active=True,
            ).first()
            grace_days = (getattr(subsidiary, 'payment_grace_days', None) or 30) if subsidiary else 30
            lang = (getattr(subsidiary, 'preferred_language', None) or 'es') if subsidiary else 'es'
        except Exception:
            grace_days = 30
            lang = 'es'

        due_date = pago.payment_date + timedelta(days=grace_days)
        if today <= due_date:
            continue

        # Dedup: no enviar si ya se envió en los últimos 7 días
        recent = CollectionEmailLog.objects.filter(
            payment_id=pago.id,
            status='sent',
            completed_at__gte=timezone.now() - timedelta(days=7)
        ).exists()
        if recent:
            continue

        recipient, proforma = resolve_collection_recipient(pago)
        if not recipient:
            logger.warning(f"[COLLECTION_SKIP] No recipient for pago={pago.pk}")
            continue

        template = resolve_template('payment.overdue', expediente.brand, lang)
        if not template:
            logger.warning(f"[COLLECTION_SKIP] No template for brand={expediente.brand}")
            continue

        # --- Render ---
        try:
            from jinja2.sandbox import SandboxedEnvironment
            context = build_notification_context(expediente, extra_context={
                'pago_amount': str(pago.amount_paid),
                'pago_fecha': pago.payment_date.isoformat(),
                'days_overdue': (today - due_date).days,
                'grace_days': grace_days,
            })
            env = SandboxedEnvironment()
            subject = env.from_string(template.subject_template).render(context)
            body = env.from_string(template.body_template).render(context)
        except Exception as exc:
            try:
                CollectionEmailLog.objects.create(
                    expediente_id=pago.expediente_id,
                    proforma_id=pago.proforma_id,
                    payment_id=pago.id,
                    grace_days_used=grace_days,
                    amount_overdue=pago.amount_paid,
                    recipient_email=recipient,
                    status='failed',
                    error=f'Render error: {str(exc)[:400]}',
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_RENDER_FAIL] pago={pago.pk}: {exc}")
            continue

        # --- Send ---
        backend = get_email_backend()
        try:
            send_result = backend.send(to=recipient, subject=subject, body=body)
        except Exception as exc:
            try:
                CollectionEmailLog.objects.create(
                    expediente_id=pago.expediente_id,
                    proforma_id=pago.proforma_id,
                    payment_id=pago.id,
                    grace_days_used=grace_days,
                    amount_overdue=pago.amount_paid,
                    recipient_email=recipient,
                    status='failed',
                    error=f'Backend exception: {str(exc)[:400]}',
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_BACKEND_FAIL] pago={pago.pk}: {exc}")
            continue

        if send_result is SendResult.SENT:
            status = 'sent'
            error_msg = ''
        elif send_result is SendResult.RETRYABLE:
            status = 'failed'
            error_msg = 'Retryable failure — will retry next cron run'
        elif send_result is SendResult.PERMANENT:
            status = 'failed'
            error_msg = 'Permanent failure'
        else:
            status = 'failed'
            error_msg = f'Unknown SendResult: {send_result}'

        try:
            with transaction.atomic():
                lock_key = _stable_lock_key(f"collection:{pago.pk}:{recipient}")
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])

                recent_sent = CollectionEmailLog.objects.filter(
                    payment_id=pago.id,
                    status='sent',
                    completed_at__gte=timezone.now() - timedelta(days=7)
                ).exists()
                if recent_sent:
                    continue

                CollectionEmailLog.objects.create(
                    expediente_id=pago.expediente_id,
                    proforma_id=pago.proforma_id,
                    payment_id=pago.id,
                    grace_days_used=grace_days,
                    amount_overdue=pago.amount_paid,
                    recipient_email=recipient,
                    status=status,
                    error=error_msg,
                    completed_at=timezone.now(),
                )
        except Exception as exc:
            try:
                CollectionEmailLog.objects.create(
                    expediente_id=pago.expediente_id,
                    proforma_id=pago.proforma_id,
                    payment_id=pago.id,
                    grace_days_used=grace_days,
                    amount_overdue=pago.amount_paid,
                    recipient_email=recipient,
                    status='failed',
                    error=str(exc)[:500],
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_FAIL] pago={pago.pk}: {exc}")
