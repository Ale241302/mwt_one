"""
Sprint 1 — Domain Logic (services.py)
Ref: LOTE_SM_SPRINT1 Item 2, ENT_OPS_STATE_MACHINE §B/§C/§F/§J/§L/§M
4 functions: create_expediente, can_transition_to, can_execute_command, execute_command
"""
import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum as models_Sum
from django.utils import timezone

from apps.expedientes.models import (
    Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine, LegalEntity,
)
from apps.expedientes.exceptions import (
    CommandValidationError, TransitionNotAllowedError, ArtifactMissingError,
)


# ══════════════════════════════════════════════════
# STATE MACHINE CONSTANTS  (ENT_OPS_STATE_MACHINE §B)
# ══════════════════════════════════════════════════

# §B1  Normal transitions
TRANSITIONS = {
    'REGISTRO':     ['PRODUCCION'],
    'PRODUCCION':   ['PREPARACION'],
    'PREPARACION':  ['DESPACHO'],
    'DESPACHO':     ['TRANSITO'],
    'TRANSITO':     ['EN_DESTINO'],
    'EN_DESTINO':   ['CERRADO'],
    'CERRADO':      [],
    'CANCELADO':    [],
}

# §B2  Cancellation allowed from
CANCEL_FROM = {'REGISTRO', 'PRODUCCION', 'PREPARACION'}

# Terminal states — no operations allowed
TERMINAL_STATES = {'CERRADO', 'CANCELADO'}

# §F1  Command ↔ required state, artifact mappings, auto-transitions
COMMAND_SPEC = {
    'C1':  {'name': 'CreateExpediente',        'event': 'expediente.created'},
    'C2':  {'name': 'RegisterOC',              'event': 'oc.registered',
            'required_state': 'REGISTRO',       'creates_art': 'ART-01'},
    'C3':  {'name': 'RegisterProforma',        'event': 'proforma.registered',
            'required_state': 'REGISTRO',       'creates_art': 'ART-02',
            'requires_art': ['ART-01']},
    'C4':  {'name': 'DecideMode',              'event': 'mode.decided',
            'required_state': 'REGISTRO',       'creates_art': 'ART-03',
            'requires_art': ['ART-02'],         'ceo_only': True},
    'C5':  {'name': 'ConfirmSAP',              'event': 'sap.confirmed',
            'required_state': 'REGISTRO',       'creates_art': 'ART-04',
            'requires_art': ['ART-01', 'ART-02', 'ART-03'],
            'auto_transition': 'PRODUCCION'},
    'C6':  {'name': 'ConfirmProduction',       'event': 'production.confirmed',
            'required_state': 'PRODUCCION',
            'transition_to': 'PREPARACION'},
    'C7':  {'name': 'RegisterShipment',        'event': 'shipment.registered',
            'required_state': 'PREPARACION',    'creates_art': 'ART-05'},
    'C8':  {'name': 'RegisterFreightQuote',    'event': 'freight_quote.registered',
            'required_state': 'PREPARACION',    'creates_art': 'ART-06',
            'requires_art': ['ART-05']},
    'C9':  {'name': 'RegisterCustoms',         'event': 'customs.registered',
            'required_state': 'PREPARACION',    'creates_art': 'ART-08',
            'requires_art': ['ART-05', 'ART-06'],
            'requires_dispatch_mode': 'MWT'},
    'C10': {'name': 'ApproveDispatch',         'event': 'dispatch.approved',
            'required_state': 'PREPARACION',    'creates_art': 'ART-07',
            'requires_art': ['ART-05', 'ART-06'],
            'auto_transition': 'DESPACHO'},
    'C11': {'name': 'ConfirmDeparture',        'event': 'departure.confirmed',
            'required_state': 'DESPACHO',
            'transition_to': 'TRANSITO'},
    'C12': {'name': 'ConfirmArrival',          'event': 'arrival.confirmed',
            'required_state': 'TRANSITO',
            'transition_to': 'EN_DESTINO'},
    'C13': {'name': 'IssueInvoice',            'event': 'invoice.issued',
            'required_state': 'EN_DESTINO',     'creates_art': 'ART-09'},
    'C14': {'name': 'CloseExpediente',         'event': 'expediente.closed',
            'required_state': 'EN_DESTINO',
            'transition_to': 'CERRADO',
            'requires_payment_paid': True,
            'requires_art': ['ART-09']},
    'C15': {'name': 'RegisterCost',            'event': 'cost.registered',
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C16': {'name': 'CancelExpediente',        'event': 'expediente.cancelled',
            'cancel_from': True,
            'transition_to': 'CANCELADO',
            'ceo_only': True,
            'bypass_block': True},
    'C17': {'name': 'BlockExpediente',         'event': 'expediente.blocked',
            'requires_unblocked': True,
            'bypass_block': True},
    'C18': {'name': 'UnblockExpediente',       'event': 'expediente.unblocked',
            'requires_blocked': True,
            'ceo_only': True,
            'bypass_block': True},
    'C21': {'name': 'RegisterPayment',         'event': 'payment.registered',
            'not_in_state': ['CERRADO', 'CANCELADO']},
}


# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def _has_artifact(expediente, art_type):
    """Check if expediente has a completed artifact of given type."""
    return expediente.artifacts.filter(
        artifact_type=art_type, status='completed'
    ).exists()


def _create_event(expediente, event_type, emitted_by, payload=None):
    """Create an EventLog entry."""
    return EventLog.objects.create(
        event_type=event_type,
        aggregate_type='expediente',
        aggregate_id=expediente.expediente_id,
        payload=payload or {},
        occurred_at=timezone.now(),
        emitted_by=emitted_by,
        correlation_id=uuid.uuid4(),
    )


# ══════════════════════════════════════════════════
# 1. create_expediente  (C1)
# ══════════════════════════════════════════════════

def create_expediente(data, user):
    """
    C1: CreateExpediente.
    Returns (expediente, event).
    FIX-3: if rule=on_creation → persist credit_clock_started_at.
    """
    legal_entity_id = data.get('legal_entity_id')
    try:
        legal_entity = LegalEntity.objects.get(entity_id=legal_entity_id)
    except LegalEntity.DoesNotExist:
        raise CommandValidationError(f'LegalEntity {legal_entity_id} not found.')

    client_id = data.get('client')
    try:
        client_entity = LegalEntity.objects.get(entity_id=client_id)
    except LegalEntity.DoesNotExist:
        raise CommandValidationError(f'Client LegalEntity {client_id} not found.')

    rule = data.get('credit_clock_start_rule', 'on_creation')

    with transaction.atomic():
        expediente = Expediente.objects.create(
            legal_entity=legal_entity,
            brand=data.get('brand', ''),
            client=client_entity,
            status='REGISTRO',
            is_blocked=False,
            mode=data.get('mode', ''),
            freight_mode=data.get('freight_mode', ''),
            transport_mode=data.get('transport_mode', ''),
            dispatch_mode=data.get('dispatch_mode', 'MWT'),
            price_basis=data.get('price_basis', ''),
            credit_clock_start_rule=rule,
            payment_status='pending',
        )

        # FIX-3: credit clock
        if rule == 'on_creation':
            expediente.credit_clock_started_at = timezone.now()
            expediente.save(update_fields=['credit_clock_started_at'])

        event = _create_event(
            expediente,
            event_type='expediente.created',
            emitted_by='C1:CreateExpediente',
            payload={'status': 'REGISTRO'},
        )

    return (expediente, event)


# ══════════════════════════════════════════════════
# 2. can_transition_to  (pure)
# ══════════════════════════════════════════════════

def can_transition_to(expediente, target_state):
    """
    Pure function → bool.  No side effects, no raises (FIX-2).
    §B: valid transitions. §E: artifact requirements.
    """
    current = expediente.status

    # Check transition is valid
    if target_state not in TRANSITIONS.get(current, []):
        return False

    # Blocked expedientes cannot transition (except cancellation handled elsewhere)
    if expediente.is_blocked:
        return False

    # Check artifact gates per state machine §E
    if target_state == 'PRODUCCION':
        # Needs ART-01, ART-02, ART-03, ART-04
        for art in ['ART-01', 'ART-02', 'ART-03', 'ART-04']:
            if not _has_artifact(expediente, art):
                return False

    elif target_state == 'DESPACHO':
        # Needs ART-05, ART-06
        for art in ['ART-05', 'ART-06']:
            if not _has_artifact(expediente, art):
                return False
        # If dispatch_mode=mwt, also needs ART-08
        if expediente.dispatch_mode == 'MWT':
            if not _has_artifact(expediente, 'ART-08'):
                return False

    elif target_state == 'CERRADO':
        # Needs ART-09 + payment_status=paid
        if not _has_artifact(expediente, 'ART-09'):
            return False
        if expediente.payment_status != 'paid':
            return False

    return True


# ══════════════════════════════════════════════════
# 3. can_execute_command  (guard — raise or pass)
# ══════════════════════════════════════════════════

def can_execute_command(expediente, command_name, user):
    """
    Guard function (FIX-2): raise exception or pass silently.
    Never returns False.
    """
    spec = COMMAND_SPEC.get(command_name)
    if not spec:
        raise CommandValidationError(f'Unknown command: {command_name}')

    # --- CEO-only check ---
    if spec.get('ceo_only') and not user.is_superuser:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(
            f'{command_name} ({spec["name"]}) requires CEO (superuser) permissions.'
        )

    # --- Block check (FIX-8: C16/C17/C18 bypass) ---
    if not spec.get('bypass_block') and expediente.is_blocked:
        raise CommandValidationError(
            f'Expediente is blocked. Cannot execute {command_name}.'
        )

    # --- State preconditions ---
    if 'required_state' in spec:
        if expediente.status != spec['required_state']:
            raise TransitionNotAllowedError(
                f'{command_name} requires status={spec["required_state"]}, '
                f'current={expediente.status}.'
            )

    if 'not_in_state' in spec:
        if expediente.status in spec['not_in_state']:
            raise TransitionNotAllowedError(
                f'{command_name} cannot execute in status={expediente.status}.'
            )

    if spec.get('cancel_from'):
        if expediente.status not in CANCEL_FROM:
            raise TransitionNotAllowedError(
                f'Cancel only allowed from {CANCEL_FROM}, '
                f'current={expediente.status}.'
            )

    # --- Block/unblock preconditions (FIX-8) ---
    if spec.get('requires_unblocked') and expediente.is_blocked:
        raise CommandValidationError(
            'Expediente is already blocked. Cannot block again.'
        )
    if spec.get('requires_blocked') and not expediente.is_blocked:
        raise CommandValidationError(
            'Expediente is not blocked. Cannot unblock.'
        )

    # --- Artifact preconditions ---
    if 'requires_art' in spec:
        for art_type in spec['requires_art']:
            if not _has_artifact(expediente, art_type):
                raise ArtifactMissingError(
                    f'{command_name} requires {art_type} to be completed.'
                )

    # --- Dispatch mode precondition ---
    if spec.get('requires_dispatch_mode'):
        if expediente.dispatch_mode != spec['requires_dispatch_mode']:
            raise CommandValidationError(
                f'{command_name} requires dispatch_mode='
                f'{spec["requires_dispatch_mode"]}, '
                f'current={expediente.dispatch_mode}.'
            )

    # --- Payment precondition (C14) ---
    if spec.get('requires_payment_paid'):
        if expediente.payment_status != 'paid':
            raise CommandValidationError(
                f'{command_name} requires payment_status=paid, '
                f'current={expediente.payment_status}.'
            )

    # All checks passed — silently return (FIX-2)


# ══════════════════════════════════════════════════
# 4. execute_command  (orchestrator)
# ══════════════════════════════════════════════════

def execute_command(expediente, command_name, data, user):
    """
    Main orchestrator. Returns (expediente, events_list).
    FIX-5: auto-transitions emit 2 events.
    FIX-3: credit clock persist only.
    """
    spec = COMMAND_SPEC.get(command_name)
    if not spec:
        raise CommandValidationError(f'Unknown command: {command_name}')

    with transaction.atomic():
        # Re-fetch with select_for_update to prevent races
        expediente = Expediente.objects.select_for_update().get(
            pk=expediente.pk
        )

        # Guard
        can_execute_command(expediente, command_name, user)

        events = []
        emitted_by = f'{command_name}:{spec["name"]}'

        # ── Artifact creation (C2-C10, C13) ──
        if 'creates_art' in spec:
            ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type=spec['creates_art'],
                status='completed',
                payload=data.get('payload', {}),
            )

        # ── Direct transition (C6, C11, C12, C14, C16) ──
        if 'transition_to' in spec:
            expediente.status = spec['transition_to']
            expediente.save(update_fields=['status'])

        # ── C15: RegisterCost ──
        if command_name == 'C15':
            CostLine.objects.create(
                expediente=expediente,
                cost_type=data['cost_type'],
                amount=data['amount'],
                currency=data['currency'],
                phase=data['phase'],
                description=data.get('description', ''),
            )

        # ── C17: BlockExpediente ──
        if command_name == 'C17':
            expediente.is_blocked = True
            expediente.blocked_reason = data.get('reason', '')
            expediente.blocked_at = timezone.now()
            expediente.blocked_by_type = 'ceo'
            expediente.blocked_by_id = str(user.pk)
            expediente.save(update_fields=[
                'is_blocked', 'blocked_reason', 'blocked_at',
                'blocked_by_type', 'blocked_by_id',
            ])

        # ── C18: UnblockExpediente ──
        if command_name == 'C18':
            expediente.is_blocked = False
            expediente.blocked_reason = None
            expediente.blocked_at = None
            expediente.blocked_by_type = None
            expediente.blocked_by_id = None
            expediente.save(update_fields=[
                'is_blocked', 'blocked_reason', 'blocked_at',
                'blocked_by_type', 'blocked_by_id',
            ])

        # ── C21: RegisterPayment + accumulation §L3 ──
        if command_name == 'C21':
            PaymentLine.objects.create(
                expediente=expediente,
                amount=data['amount'],
                currency=data['currency'],
                method=data['method'],
                reference=data['reference'],
                registered_at=timezone.now(),
                registered_by_type='ceo',
                registered_by_id=str(user.pk),
            )
            # Accumulation: §L3
            _update_payment_status(expediente)

        # ── C7: Credit clock FIX-3 ──
        if command_name == 'C7':
            if expediente.credit_clock_start_rule == 'on_shipment':
                expediente.credit_clock_started_at = timezone.now()
                expediente.save(update_fields=['credit_clock_started_at'])

        # ── Primary event ──
        event1 = _create_event(
            expediente,
            event_type=spec['event'],
            emitted_by=emitted_by,
            payload={'status': expediente.status},
        )
        events.append(event1)

        # ── Auto-transition (FIX-5: C5→PRODUCCION, C10→DESPACHO) ──
        if 'auto_transition' in spec:
            target = spec['auto_transition']
            if can_transition_to(expediente, target):
                expediente.status = target
                expediente.save(update_fields=['status'])
                event2 = _create_event(
                    expediente,
                    event_type='expediente.state_changed',
                    emitted_by=emitted_by,
                    payload={
                        'from': spec.get('required_state', ''),
                        'to': target,
                    },
                )
                events.append(event2)

    return (expediente, events)


# ══════════════════════════════════════════════════
# INTERNAL: Payment accumulation (§L3)
# ══════════════════════════════════════════════════


def _update_payment_status(expediente):
    """
    §L3: SUM(payments) >= invoice_total → paid.
    §M: 1 currency per expediente. Overpayment = paid.
    """
    total_paid = expediente.payment_lines.aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    # Get invoice total from ART-09 payload
    invoice_total = Decimal('0')
    art09 = expediente.artifacts.filter(
        artifact_type='ART-09', status='completed'
    ).first()
    if art09 and 'total' in art09.payload:
        invoice_total = Decimal(str(art09.payload['total']))

    if invoice_total <= 0:
        # No invoice yet or zero — keep status as-is or pending
        if total_paid > 0:
            expediente.payment_status = 'partial'
        else:
            expediente.payment_status = 'pending'
    elif total_paid >= invoice_total:
        expediente.payment_status = 'paid'
    elif total_paid > 0:
        expediente.payment_status = 'partial'
    else:
        expediente.payment_status = 'pending'

    expediente.save(update_fields=['payment_status'])


# ══════════════════════════════════════════════════
# C19 & C20: Artifact Correction (Sprint 2)
# ══════════════════════════════════════════════════

def _check_post_transition_block(expediente, artifact_type):
    """
    Check if the artifact was a precondition for an executed transition.
    If yes, block the Expediente.
    MVP heuristic: If the Expediente's current state is beyond the state
    where this artifact usually gets generated, we block it.
    """
    created_in_state = None
    for cmd, spec in COMMAND_SPEC.items():
        if spec.get('creates_art') == artifact_type:
            created_in_state = spec.get('required_state')
            break
            
    if created_in_state and expediente.status != created_in_state:
        if not expediente.is_blocked:
            expediente.is_blocked = True
            expediente.blocked_reason = f"Artifact {artifact_type} was corrected/voided while in downstream state {expediente.status}."
            expediente.blocked_at = timezone.now()
            expediente.blocked_by_type = 'SYSTEM'
            expediente.blocked_by_id = 'ARTIFACT_CORRECTION'
            expediente.save(update_fields=['is_blocked', 'blocked_reason', 'blocked_at', 'blocked_by_type', 'blocked_by_id'])
            
            _create_event(
                expediente,
                event_type='BLOCKED_POR_CAMBIO_PRECONDICION',
                emitted_by='SYSTEM:ARTIFACT_CORRECTION',
                payload={'artifact_type': artifact_type}
            )

def supersede_artifact(old_artifact_id, new_payload, user):
    with transaction.atomic():
        try:
            old_art = ArtifactInstance.objects.select_for_update().get(pk=old_artifact_id)
        except ArtifactInstance.DoesNotExist:
            raise CommandValidationError("Artifact not found")
            
        expediente = Expediente.objects.select_for_update().get(pk=old_art.expediente_id)
        
        if old_art.status != 'COMPLETED':
            raise CommandValidationError(f"Cannot supersede artifact in status {old_art.status}")
            
        if expediente.status in TERMINAL_STATES:
            raise CommandValidationError("Cannot supersede artifact in terminal state Expediente")

        new_art = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type=old_art.artifact_type,
            status='COMPLETED',
            payload=new_payload,
            supersedes=old_art
        )
        
        old_art.status = 'SUPERSEDED'
        old_art.superseded_by = new_art
        old_art.save(update_fields=['status', 'superseded_by'])
        
        event = _create_event(
            expediente,
            event_type='artifact.superseded',
            emitted_by='C19:SupersedeArtifact',
            payload={
                'old_artifact_id': str(old_art.artifact_id),
                'new_artifact_id': str(new_art.artifact_id),
            }
        )
        
        _check_post_transition_block(expediente, old_art.artifact_type)
        return expediente, new_art, event


def void_artifact(old_artifact_id, user):
    with transaction.atomic():
        try:
            old_art = ArtifactInstance.objects.select_for_update().get(pk=old_artifact_id)
        except ArtifactInstance.DoesNotExist:
            raise CommandValidationError("Artifact not found")
            
        expediente = Expediente.objects.select_for_update().get(pk=old_art.expediente_id)
        
        if old_art.artifact_type != 'ART-09':
            raise CommandValidationError("Only ART-09 can be voided in MVP.")
            
        if old_art.status != 'COMPLETED':
            raise CommandValidationError(f"Cannot void artifact in status {old_art.status}")
            
        if expediente.status in TERMINAL_STATES:
            raise CommandValidationError("Cannot void artifact in terminal state Expediente")

        old_art.status = 'VOID'
        old_art.save(update_fields=['status'])
        
        event = _create_event(
            expediente,
            event_type='artifact.voided',
            emitted_by='C20:VoidArtifact',
            payload={
                'artifact_id': str(old_art.artifact_id),
            }
        )
        
        _check_post_transition_block(expediente, old_art.artifact_type)
        return expediente, old_art, event


# ══════════════════════════════════════════════════
# UI HELPERS (Sprint 3)
# ══════════════════════════════════════════════════

def get_available_commands(expediente, user):
    """
    Returns a list of command IDs (e.g., ['C2', 'C3', 'C15']) that the given user
    can execute on the given expediente in its current state.
    """
    available = []
    for cmd in COMMAND_SPEC.keys():
        if cmd == 'C1':
            continue
        try:
            can_execute_command(expediente, cmd, user)
            available.append(cmd)
        except Exception:
            # If any validation error is raised, the command is not available
            pass
            
    return available
