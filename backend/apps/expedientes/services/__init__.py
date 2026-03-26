import uuid
import logging
from django.utils import timezone
from django.db import transaction
from apps.expedientes.models import Expediente, ArtifactInstance, EventLog
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CommandValidationError

from .constants import COMMAND_SPEC
from .commands.c1 import handle_c1
from .commands.c2 import handle_c2
from .commands.c3 import handle_c3
from .commands.c4 import handle_c4
from .commands.c5 import handle_c5
from .commands.c6 import handle_c6
from .commands.c7 import handle_c7
from .commands.c8 import handle_c8
from .commands.c9 import handle_c9
from .commands.c10 import handle_c10
from .commands.c11 import handle_c11
from .commands.c11b import handle_c11b
from .commands.c12 import handle_c12
from .commands.c13 import handle_c13
from .commands.c14 import handle_c14
from .commands.c15 import handle_c15
from .commands.c16 import handle_c16
from .commands.c_cancel import handle_cancel
from .commands.c21 import handle_c21

# Restoring original others
from .commands_destino import handle_c22
from .financial import handle_c21 as handle_c21_fin
from .exceptions import handle_c17, handle_c18
from .corrections import handle_c19, handle_c20, supersede_artifact, void_artifact, register_compensation
from .logistics import handle_c23, handle_c24, handle_c30, add_shipment_update
from .queries import (
    get_available_commands, get_costs,
    get_costs_summary, get_invoice_suggestion, get_invoice,
    calculate_financial_comparison, get_logistics_suggestions,
    get_handoff_suggestion, get_liquidation_payment_suggestion
)
from .reporting import generate_mirror_pdf

create_expediente = handle_c1

logger = logging.getLogger(__name__)

# Registry of handlers
HANDLERS = {
    'C1': handle_c1,
    'C2': handle_c2, 'C3': handle_c3, 'C4': handle_c4, 'C5': handle_c5,
    'C6': handle_c6,
    'C7': handle_c7, 'C8': handle_c8, 'C9': handle_c9, 'C10': handle_c10, 'C11': handle_c11,
    'C11B': handle_c11b,
    'C12': handle_c12,
    'C13': handle_c13, 'C14': handle_c14,
    'C15': handle_c15,
    'C16': handle_c16,
    'CANCEL': handle_cancel,
    'REOPEN': handle_reopen,
    
    # Restoring original others
    'C22': handle_c22,
    'C21': handle_c21,
    'C25': handle_c21_fin,
    'C17': handle_c17, 'C18': handle_c18,
    'C19': handle_c19, 'C20': handle_c20,
    'C23': handle_c23, 'C24': handle_c24, 'C30': handle_c30
}

from .state_machine import can_transition_to

def can_execute_command(expediente, cmd_id, user):
    return can_transition_to(expediente, cmd_id, user)


def execute_command(expediente, cmd_id, payload, user):
    """
    Main entry point for command execution.
    Handles validation, atomic transaction, artifact creation, and status transitions.
    """
    can_exec, reason = can_execute_command(expediente, cmd_id, user)
    if not can_exec:
        raise Exception(reason)

    spec = COMMAND_SPEC.get(cmd_id)
    handler = HANDLERS.get(cmd_id)
    
    events = []

    with transaction.atomic():
        # 1. Artifact creation (Optional)
        new_artifact = None
        if spec.get('creates_art'):
            new_artifact = ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type=spec['creates_art'],
                payload=payload.get('payload', payload),
                status=ArtifactStatusEnum.COMPLETED
            )
            
        # 2. Handler execution
        if handler:
            env = {'user': user}
            handler(expediente, payload, env=env)
            
        # 3. Status Transition
        old_status = expediente.status
        new_status = spec.get('transition_to')
        if new_status and old_status != new_status:
            expediente.status = new_status
            expediente.save()
            
            # Transition Event
            ev_trans = EventLog.objects.create(
                event_type='expediente.status_changed',
                aggregate_type='expediente',
                aggregate_id=expediente.expediente_id,
                payload={'old': old_status, 'new': new_status},
                occurred_at=timezone.now(),
                emitted_by='SYSTEM',
                correlation_id=uuid.uuid4()
            )
            events.append(ev_trans)

        # 4. Command Event
        ev_cmd = EventLog.objects.create(
            event_type=f'command.{cmd_id}',
            aggregate_type='expediente',
            aggregate_id=expediente.expediente_id,
            payload={
                'command': cmd_id,
                'artifact_id': str(new_artifact.pk) if new_artifact else None
            },
            occurred_at=timezone.now(),
            emitted_by=cmd_id,
            correlation_id=uuid.uuid4()
        )
        events.append(ev_cmd)
        
    return expediente, events

# Re-exposing symbols for Sprint 12 API
register_oc = handle_c2
register_proforma = handle_c3
decide_mode = handle_c4
confirm_sap = handle_c5
confirm_production = handle_c6
register_shipment = handle_c7
register_freight_quote = handle_c8
register_customs = handle_c9
approve_dispatch = handle_c10
confirm_departure = handle_c11
confirm_arrival = handle_c12
issue_invoice = handle_c13
close_expediente = handle_c14
register_cost = handle_c15
cancel_expediente = handle_c16
block_expediente = handle_c17
unblock_expediente = handle_c18
register_rectification = handle_c19
register_void = handle_c20
register_payment = handle_c21
register_liquidation = handle_c22
register_shipment_update = handle_c23
register_generic_artifact = handle_c30
register_compensation = register_compensation # already imported
