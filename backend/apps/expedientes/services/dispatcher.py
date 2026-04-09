# Sprint 18 - T0.5: post_command_hooks en dispatcher
# Sprint 21: el hook s21_eventlog_hook puebla los 5 campos nuevos de EventLog.

import uuid
from datetime import timezone as dt_timezone
from django.utils import timezone

post_command_hooks = []  # Lista modulo-level. Registrar hooks aqui.


def register_hook(fn):
    """Registrar una funcion hook. Sera invocada post-command exitoso."""
    if fn not in post_command_hooks:
        post_command_hooks.append(fn)
    return fn


def dispatch_with_hooks(expediente, command_code, user, handler_fn, **kwargs):
    """
    Ejecuta handler_fn y luego los hooks registrados.
    Los hooks NO se invocan si handler_fn lanza excepcion.
    """
    result = handler_fn(expediente, user, **kwargs)
    for hook in post_command_hooks:
        try:
            hook(
                expediente=expediente,
                command_code=command_code,
                user=user,
                result=result,
            )
        except Exception:
            pass  # hooks no deben romper el flujo principal
    return result


# === S21: Hook que crea EventLog con campos nuevos ===
def s21_eventlog_hook(expediente, command_code, user, result, **kwargs):
    """
    Hook post-command que crea un EventLog con los 5 campos nuevos de S21.

    action_source: usa command_code (ej: 'C1', 'C5').
    previous_status / new_status: poblados si el result tiene esa info.
    proforma: poblado si result es un ArtifactInstance de tipo ART-02.
    user: el usuario que ejecuto el command (None para Celery/system).

    REGLA: action_source contrato cerrado — solo valores definidos en el sprint.
    """
    from apps.expedientes.models import EventLog, ArtifactInstance

    # Detectar si hubo cambio de estado
    prev_status = getattr(result, '_prev_status', None) if result else None
    new_status = getattr(result, '_new_status', None) if result else None

    # Detectar si el result es una proforma (ART-02)
    proforma = None
    if isinstance(result, ArtifactInstance) and result.artifact_type == 'ART-02':
        proforma = result

    EventLog.objects.create(
        event_type=f'command.executed',
        aggregate_type='EXP',
        aggregate_id=expediente.expediente_id,
        payload={},  # payload interno vacio por defecto
        occurred_at=timezone.now(),
        emitted_by=f'{command_code}:hook',
        processed_at=timezone.now(),
        retry_count=0,
        correlation_id=uuid.uuid4(),
        # S21 campos nuevos
        user=user if user and user.is_authenticated else None,
        proforma=proforma,
        action_source=command_code,  # Ej: 'C1', 'C5', 'create_proforma'
        previous_status=prev_status,
        new_status=new_status,
    )



# Auto-registrar el hook S21
register_hook(s21_eventlog_hook)


# === S26: Hook que encola send_notification ===
def notify_on_command(expediente, command_code, user, result, **kwargs):
    """
    Hook post-command que encola send_notification si el command_code tiene template.
    Si el hook falla → el comando sigue siendo exitoso (no bloquear).
    event_log_id: el EventLog fue creado por s21_eventlog_hook antes de este hook.
    """
    from apps.notifications.mappings import TRIGGER_TO_TEMPLATE

    template_key = TRIGGER_TO_TEMPLATE.get(command_code)
    if not template_key:
        return  # comando no mapeado — no notification

    # Obtener el event_log_id creado por s21_eventlog_hook
    # El log más reciente para este expediente+action_source
    try:
        from apps.expedientes.models import EventLog, ArtifactInstance
        from apps.notifications.tasks import send_notification

        event_log = EventLog.objects.filter(
            expediente=expediente,
            action_source=command_code,
        ).order_by('-occurred_at').first()

        event_log_id = str(event_log.event_id) if event_log else None

        # Detectar proforma si el result es ArtifactInstance ART-02
        proforma_id = None
        if isinstance(result, ArtifactInstance) and result.artifact_type == 'ART-02':
            proforma_id = str(result.artifact_id)

        send_notification.delay(
            template_key=template_key,
            expediente_id=str(expediente.expediente_id),
            proforma_id=proforma_id,
            event_log_id=event_log_id,
            trigger_action_source=command_code,
            extra_context={},
        )
    except Exception as exc:
        # Hook failure no debe bloquear el comando principal
        import logging
        logging.getLogger(__name__).warning(f"[NOTIF_HOOK] Failed for {command_code}: {exc}")


# Auto-registrar el hook S26
register_hook(notify_on_command)
