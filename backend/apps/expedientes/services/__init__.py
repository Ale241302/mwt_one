import logging
from django.db import transaction
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CommandValidationError

from .constants import COMMAND_SPEC
from .create import handle_c1
create_expediente = handle_c1
from .commands_registro import handle_c2, handle_c3, handle_c4, handle_c5
from .commands_produccion import handle_c6
from .commands_preparacion import handle_c7, handle_c8, handle_c9, handle_c10, handle_c11
from .commands_transito import handle_c12
from .commands_destino import handle_c13, handle_c14, handle_c22
from .financial import handle_c15, handle_c21
from .exceptions import handle_c16, handle_c17, handle_c18
from .corrections import handle_c19, handle_c20, supersede_artifact, void_artifact
from .logistics import handle_c23, handle_c24, handle_c30
from .queries import (
    can_execute_command, get_available_commands, get_costs,
    get_costs_summary, get_invoice_suggestion, get_invoice,
    calculate_financial_comparison
)
from .reporting import generate_mirror_pdf

logger = logging.getLogger(__name__)

# Registry of handlers
HANDLERS = {
    'C2': handle_c2, 'C3': handle_c3, 'C4': handle_c4, 'C5': handle_c5,
    'C6': handle_c6,
    'C7': handle_c7, 'C8': handle_c8, 'C9': handle_c9, 'C10': handle_c10, 'C11': handle_c11,
    'C12': handle_c12,
    'C13': handle_c13, 'C14': handle_c14, 'C22': handle_c22,
    'C15': handle_c15, 'C21': handle_c21,
    'C16': handle_c16, 'C17': handle_c17, 'C18': handle_c18,
    'C19': handle_c19, 'C20': handle_c20,
    'C23': handle_c23, 'C24': handle_c24, 'C30': handle_c30
}

def execute_command(expediente, cmd_id, payload):
    """
    Modular orchestrator for command execution.
    """
    if cmd_id not in COMMAND_SPEC:
        raise CommandValidationError(f"Unknown command: {cmd_id}")

    cmd_config = COMMAND_SPEC[cmd_id]
    
    # 1. Validation (Requires Status)
    req_status = cmd_config.get('requires_status')
    if req_status and expediente.status != req_status:
        raise CommandValidationError(
            f"Command {cmd_id} requires status {req_status}. Current: {expediente.status}"
        )

    # 2. Blocked check
    if expediente.is_blocked and cmd_id not in ['C18', 'C19', 'C20']:
        raise CommandValidationError("Expediente is BLOCKED. Action not allowed.")

    handler = HANDLERS.get(cmd_id)
    
    with transaction.atomic():
        # Dispatch specific logic
        if handler:
            handler(expediente, payload)
        
        # 3. Generic Artifact Creation
        creates_art = cmd_config.get('creates_art')
        if creates_art:
            # S4 Logic: generic artifacts (not ART-11/ART-10 managed specifically)
            if cmd_id not in ['C30', 'C22']:
                ArtifactInstance.objects.create(
                    expediente=expediente,
                    artifact_type=creates_art,
                    status=ArtifactStatusEnum.COMPLETED,
                    payload=payload
                )

        # 4. Generic Status Transition
        transition_to = cmd_config.get('transition_to')
        if transition_to:
            expediente.status = transition_to
            expediente.save()

    return expediente
