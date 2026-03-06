"""
Sprint 1-4 — Domain Logic (services.py)
Ref: LOTE_SM_SPRINT1 Item 2, ENT_OPS_STATE_MACHINE §B/§C/§F/§J/§L/§M
Sprint 4: Costs doble vista, ART-09 invoice, financial comparison,
          ART-19 logistics, Tecmater brand logic, mirror PDF
"""
import uuid
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum as models_Sum, Max as models_Max
from django.utils import timezone

from apps.expedientes.models import (
    Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine,
    LegalEntity, LogisticsOption,
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

# Sprint 4 S4-09: Tecmater has a special transition map
TRANSITIONS_TECMATER = {
    'REGISTRO':     ['PREPARACION'],   # Skip PRODUCCION
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
            'bypass_block': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C18': {'name': 'UnblockExpediente',       'event': 'expediente.unblocked',
            'requires_blocked': True,
            'ceo_only': True,
            'bypass_block': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C21': {'name': 'RegisterPayment',         'event': 'payment.registered',
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C19': {'name': 'SupersedeArtifact',       'event': 'artifact.superseded',
            'ceo_only': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C20': {'name': 'VoidArtifact',            'event': 'artifact.voided',
            'ceo_only': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
    # Sprint 4 S4-07: ART-19 Logistics Decision
    'C22': {'name': 'MaterializeLogistics',    'event': 'logistics.materialized',
            'creates_art': 'ART-19',
            'not_in_state': ['CERRADO', 'CANCELADO', 'REGISTRO', 'DESPACHO', 'TRANSITO', 'EN_DESTINO']},
    'C23': {'name': 'AddLogisticsOption',      'event': 'logistics.option_added',
            'ceo_only': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
    'C24': {'name': 'DecideLogistics',         'event': 'logistics.decided',
            'ceo_only': True,
            'not_in_state': ['CERRADO', 'CANCELADO']},
}

# Sprint 4 S4-09: Tecmater skip artifacts
TECMATER_SKIP_ARTIFACTS = {'ART-03', 'ART-04', 'ART-10', 'ART-19'}
TECMATER_BLOCKED_COMMANDS = {'C4', 'C5'}  # DecideMode, ConfirmSAP


# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def _has_artifact(expediente, art_type):
    """Check if expediente has a completed artifact of given type."""
    return expediente.artifacts.filter(
        artifact_type=art_type, status='completed'
    ).exists()


def _has_artifact_any_status(expediente, art_type, statuses):
    """Check if expediente has an artifact of given type in any of the given statuses."""
    return expediente.artifacts.filter(
        artifact_type=art_type, status__in=statuses
    ).exists()


def _get_artifact(expediente, art_type):
    """Get latest completed artifact of given type."""
    return expediente.artifacts.filter(
        artifact_type=art_type, status='completed'
    ).order_by('-created_at').first()


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


def _is_tecmater(expediente):
    """Check if expediente is Tecmater brand."""
    if hasattr(expediente, 'brand') and hasattr(expediente.brand, 'slug'):
        return expediente.brand.slug == 'tecmater'
    return expediente.brand == 'TECMATER'
    
def get_required_artifacts(expediente):
    try:
        from apps.brands.services import BrandService
        brand_id = expediente.brand_id
        if not brand_id:
            return None
        return BrandService.get_artifact_flow(brand_id, getattr(expediente, 'destination', 'CR'))
    except Exception:
        return None


# ══════════════════════════════════════════════════
# 1. create_expediente  (C1)
# ══════════════════════════════════════════════════

def create_expediente(data, user):
    """
    C1: CreateExpediente.
    Returns (expediente, event).
    Sprint 4 S4-09: brand=tecmater forces mode=FULL
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
    brand_id = data.get('brand', 'marluvas')
    destination = data.get('destination', 'CR')
    mode = data.get('mode', '')

    # Sprint 4 S4-09: Tecmater forces FULL mode
    if brand_id in ('TECMATER', 'tecmater'):
        if mode and mode.upper() == 'COMISION':
            raise CommandValidationError(
                'Tecmater brand does not support COMISION mode. Mode forced to FULL.'
            )
        mode = 'FULL'

    with transaction.atomic():
        expediente = Expediente.objects.create(
            legal_entity=legal_entity,
            brand_id=brand_id,
            destination=destination,
            client=client_entity,
            status='REGISTRO',
            is_blocked=False,
            mode=mode,
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
            payload={'status': 'REGISTRO', 'brand': brand_id, 'destination': destination, 'mode': mode},
        )

    return (expediente, event)


# ══════════════════════════════════════════════════
# 2. can_transition_to  (pure)
# ══════════════════════════════════════════════════

def can_transition_to(expediente, target_state):
    """
    Pure function → bool.  No side effects, no raises (FIX-2).
    §B: valid transitions. §E: artifact requirements.
    Sprint 4 S4-09: Tecmater uses TRANSITIONS_TECMATER
    """
    current = expediente.status
    is_tec = _is_tecmater(expediente)

    # Choose transition map by brand
    transitions = TRANSITIONS_TECMATER if is_tec else TRANSITIONS

    # Check transition is valid
    if target_state not in transitions.get(current, []):
        return False

    # Blocked expedientes cannot transition (except cancellation handled elsewhere)
    if expediente.is_blocked:
        return False

    # Check artifact gates per state machine §E
    flow = get_required_artifacts(expediente)
    
    if target_state == 'PRODUCCION':
        # Marluvas needs ART-01, ART-02, ART-03, ART-04
        for art in ['ART-01', 'ART-02', 'ART-03', 'ART-04']:
            if flow is not None and art not in flow: continue
            if not _has_artifact(expediente, art):
                return False

    elif target_state == 'PREPARACION':
        if is_tec:
            # Tecmater: only needs ART-01, ART-02 to go REGISTRO→PREPARACION
            for art in ['ART-01', 'ART-02']:
                if flow is not None and art not in flow: continue
                if not _has_artifact(expediente, art):
                    return False
        else:
            # Marluvas: comes from PRODUCCION, no extra artifact gate
            pass

    elif target_state == 'DESPACHO':
        # Needs ART-05, ART-06
        for art in ['ART-05', 'ART-06']:
            if flow is not None and art not in flow: continue
            if not _has_artifact(expediente, art):
                return False
        # If dispatch_mode=mwt, also needs ART-08
        if expediente.dispatch_mode == 'MWT':
            if flow is None or 'ART-08' in flow:
                if not _has_artifact(expediente, 'ART-08'):
                    return False

    elif target_state == 'CERRADO':
        if is_tec or expediente.mode == 'COMISION':
            # COMISION / Tecmater: only needs payment_status=paid (not ART-09)
            if expediente.payment_status != 'paid':
                return False
            # COMISION doesn't require ART-09
            if not is_tec and expediente.mode != 'COMISION':
                if flow is None or 'ART-09' in flow:
                    if not _has_artifact(expediente, 'ART-09'):
                        return False
        else:
            # FULL Marluvas: needs ART-09 + payment_status=paid
            if flow is None or 'ART-09' in flow:
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
    Sprint 4 S4-09: Tecmater blocks C4, C5
    """
    spec = COMMAND_SPEC.get(command_name)
    if not spec:
        raise CommandValidationError(f'Unknown command: {command_name}')

    # Sprint 4 S4-09: Tecmater blocks certain commands
    if _is_tecmater(expediente) and command_name in TECMATER_BLOCKED_COMMANDS:
        from rest_framework.exceptions import APIException
        class Conflict409(APIException):
            status_code = 409
            default_detail = f'{command_name} ({spec["name"]}) is not applicable for Tecmater brand.'
        raise Conflict409()

    # Sprint 4 S4-03: C13 blocked for COMISION mode
    if command_name == 'C13' and expediente.mode == 'COMISION':
        from rest_framework.exceptions import APIException
        class Conflict409(APIException):
            status_code = 409
            default_detail = 'ART-09 not applicable for mode COMISION. Marluvas factura directo.'
        raise Conflict409()

    # --- CEO-only check ---
    # BUG 6: Bypass if user is None (SYSTEM actor)
    if user is not None and spec.get('ceo_only') and not user.is_superuser:
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
        flow = get_required_artifacts(expediente)
        for art_type in spec['requires_art']:
            if flow is not None and art_type not in flow:
                continue
            # Sprint 4 S4-09: Skip Tecmater blocked artifacts
            if _is_tecmater(expediente) and art_type in TECMATER_SKIP_ARTIFACTS:
                continue
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

    # --- C14: COMISION does not require ART-09 ---
    if command_name == 'C14' and expediente.mode == 'COMISION':
        # Only requires payment_status=paid + ART-01 exists
        if not _has_artifact(expediente, 'ART-01'):
            raise ArtifactMissingError('C14 requires ART-01 for COMISION mode.')

    # --- C22 specific: requires ART-04 ---
    if command_name == 'C22':
        if _is_tecmater(expediente):
            from rest_framework.exceptions import APIException
            class Conflict409(APIException):
                status_code = 409
                default_detail = 'ART-19 is not applicable for Tecmater brand.'
            raise Conflict409()
        if not _has_artifact(expediente, 'ART-04'):
            raise ArtifactMissingError('C22 requires ART-04 to be completed.')
        if expediente.status not in ('PRODUCCION', 'PREPARACION'):
            raise TransitionNotAllowedError(
                f'C22 requires status PRODUCCION or PREPARACION, current={expediente.status}.'
            )

    # --- C23 specific: requires ART-19 pending ---
    if command_name == 'C23':
        art19 = expediente.artifacts.filter(
            artifact_type='ART-19', status='pending'
        ).first()
        if not art19:
            raise ArtifactMissingError('C23 requires ART-19 with status=pending.')

    # --- C24 specific: requires ART-19 pending + options ---
    if command_name == 'C24':
        art19 = expediente.artifacts.filter(
            artifact_type='ART-19', status='pending'
        ).first()
        if not art19:
            raise ArtifactMissingError('C24 requires ART-19 with status=pending.')
        if not art19.logistics_options.exists():
            raise CommandValidationError(
                'C24 requires at least 1 logistics option before deciding.'
            )

    # All checks passed — silently return (FIX-2)


# ══════════════════════════════════════════════════
# 4. execute_command  (orchestrator)
# ══════════════════════════════════════════════════

def execute_command(expediente, command_name, data, user):
    """
    Main orchestrator. Returns (expediente, events_list).
    Sprint 4: Extended for C13 enriched, C15 visibility, C22/C23/C24,
              Tecmater auto-transition logic.
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

        # ── C13: IssueInvoice (Sprint 4 enriched) ──
        if command_name == 'C13':
            _handle_issue_invoice(expediente, data, emitted_by, events)
        # ── Standard artifact creation (C2-C10, except C13) ──
        elif 'creates_art' in spec and command_name not in ('C22',):
            ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type=spec['creates_art'],
                status='completed',
                payload=data.get('payload', {}),
            )

        # ── Direct transition (C6, C11, C12, C14, C16) ──
        if 'transition_to' in spec:
            # Sprint 4: C14 for COMISION doesn't need ART-09
            if command_name == 'C14' and expediente.mode == 'COMISION':
                # Skip ART-09 check, just transition
                pass
            expediente.status = spec['transition_to']
            expediente.save(update_fields=['status'])

        # ── C15: RegisterCost (Sprint 4: with visibility) ──
        if command_name == 'C15':
            CostLine.objects.create(
                expediente=expediente,
                cost_type=data['cost_type'],
                amount=data['amount'],
                currency=data['currency'],
                phase=data['phase'],
                description=data.get('description', ''),
                visibility=data.get('visibility', 'internal'),
            )

        # ── C17: BlockExpediente ──
        if command_name == 'C17':
            expediente.is_blocked = True
            expediente.blocked_reason = data.get('reason', '')
            expediente.blocked_at = timezone.now()
            expediente.blocked_by_type = data.get('actor_type', 'ceo')
            expediente.blocked_by_id = str(user.pk) if user else data.get('actor_id', 'SYSTEM')
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
                registered_by_type='ceo' if user else 'system',
                registered_by_id=str(user.pk) if user else 'SYSTEM',
            )
            _update_payment_status(expediente)

        # ── C7: Credit clock FIX-3 ──
        if command_name == 'C7':
            if expediente.credit_clock_start_rule == 'on_shipment':
                expediente.credit_clock_started_at = timezone.now()
                expediente.save(update_fields=['credit_clock_started_at'])

        # ── C22: MaterializeLogistics (Sprint 4) ──
        if command_name == 'C22':
            _handle_materialize_logistics(expediente, data, emitted_by, events)

        # ── C23: AddLogisticsOption (Sprint 4) ──
        if command_name == 'C23':
            _handle_add_logistics_option(expediente, data, emitted_by, events)

        # ── C24: DecideLogistics (Sprint 4) ──
        if command_name == 'C24':
            _handle_decide_logistics(expediente, data, emitted_by, events)

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

        # ── Sprint 4 S4-09: Tecmater auto-transition after ART-02 ──
        # If Tecmater, after C3 (RegisterProforma), check if we can skip to PREPARACION
        if _is_tecmater(expediente) and command_name == 'C3':
            if can_transition_to(expediente, 'PREPARACION'):
                expediente.status = 'PREPARACION'
                expediente.save(update_fields=['status'])
                event_tec = _create_event(
                    expediente,
                    event_type='expediente.state_changed',
                    emitted_by=emitted_by,
                    payload={
                        'from': 'REGISTRO',
                        'to': 'PREPARACION',
                        'reason': 'Tecmater skip PRODUCCION',
                    },
                )
                events.append(event_tec)

    return (expediente, events)


# ══════════════════════════════════════════════════
# Sprint 4 S4-03: C13 IssueInvoice enriched handler
# ══════════════════════════════════════════════════

def _handle_issue_invoice(expediente, data, emitted_by, events):
    """
    Sprint 4: Enriched C13 handler.
    - Auto-generates consecutive MWT-YYYY-NNNN
    - Builds doble vista payload
    - Stores in ArtifactInstance.payload (no new model)
    """
    # Generate consecutive
    year = timezone.now().year
    last_consecutive = ArtifactInstance.objects.filter(
        artifact_type='ART-09',
        status='completed',
        payload__consecutive__startswith=f'MWT-{year}-'
    ).count()
    consecutive = f'MWT-{year}-{str(last_consecutive + 1).zfill(4)}'

    # Get cost totals
    total_internal = expediente.cost_lines.aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    total_client_costs = expediente.cost_lines.filter(
        visibility='client'
    ).aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    # Client-facing total from input (CEO decides final price)
    total_client_view = Decimal(str(data.get('total_client_view',
                                             data.get('payload', {}).get('total_client_view', 0))))
    currency = data.get('currency', data.get('payload', {}).get('currency', 'USD'))

    # Calculate margin
    margin = total_client_view - total_internal
    margin_pct = (margin / total_client_view * 100) if total_client_view > 0 else Decimal('0')

    # Build payload
    payload = {
        'consecutive': consecutive,
        'lines': data.get('payload', {}).get('lines', []),
        'total_client_view': float(total_client_view),
        'total_internal_view': float(total_internal),  # [CEO-ONLY]
        'currency': currency,
        'issued_to': data.get('payload', {}).get('issued_to', str(expediente.client_id)),
        'margin': float(margin),           # [CEO-ONLY]
        'margin_pct': float(margin_pct),   # [CEO-ONLY]
        'total': float(total_client_view),  # For backward compat with payment accumulation
    }

    ArtifactInstance.objects.create(
        expediente=expediente,
        artifact_type='ART-09',
        status='completed',
        payload=payload,
    )


# ══════════════════════════════════════════════════
# Sprint 4 S4-07: ART-19 Logistics Decision handlers
# ══════════════════════════════════════════════════

def _handle_materialize_logistics(expediente, data, emitted_by, events):
    """C22: Create ART-19 with snapshots of ART-01 and ART-04."""
    art01 = _get_artifact(expediente, 'ART-01')
    art04 = _get_artifact(expediente, 'ART-04')

    payload = {
        'snapshot_art01': art01.payload if art01 else {},
        'snapshot_art04': art04.payload if art04 else {},
        'status': 'pending',
        'options_count': 0,
    }

    ArtifactInstance.objects.create(
        expediente=expediente,
        artifact_type='ART-19',
        status='pending',
        payload=payload,
    )


def _handle_add_logistics_option(expediente, data, emitted_by, events):
    """C23: Add LogisticsOption to ART-19."""
    art19 = expediente.artifacts.filter(
        artifact_type='ART-19', status='pending'
    ).first()

    option_count = art19.logistics_options.count()
    option_id = data.get('option_id', f'OPT-{option_count + 1}')

    LogisticsOption.objects.create(
        artifact_instance=art19,
        option_id=option_id,
        mode=data['mode'],
        carrier=data['carrier'],
        route=data['route'],
        estimated_days=data['estimated_days'],
        estimated_cost=data['estimated_cost'],
        currency=data['currency'],
        valid_until=data.get('valid_until'),
        source=data.get('source', 'manual'),
    )

    # Update ART-19 payload
    art19.payload['options_count'] = option_count + 1
    art19.save(update_fields=['payload'])


def _handle_decide_logistics(expediente, data, emitted_by, events):
    """C24: Select logistics option, complete ART-19."""
    art19 = expediente.artifacts.filter(
        artifact_type='ART-19', status='pending'
    ).first()

    selected_option_id = data['selected_option_id']
    try:
        option = art19.logistics_options.get(option_id=selected_option_id)
    except LogisticsOption.DoesNotExist:
        raise CommandValidationError(
            f'Logistics option {selected_option_id} not found.'
        )

    option.is_selected = True
    # LogisticsOption extends TimestampMixin, not AppendOnlyModel, so save is OK
    LogisticsOption.objects.filter(pk=option.pk).update(is_selected=True)

    art19.status = 'completed'
    art19.payload.update({
        'selected_option_id': selected_option_id,
        'decided_by': str(user.pk) if (user := None) else 'CEO',  # Will be set properly
        'decided_at': timezone.now().isoformat(),
    })
    art19.save(update_fields=['status', 'payload'])


# ══════════════════════════════════════════════════
# INTERNAL: Payment accumulation (§L3)
# Sprint 4: Support COMISION mode (reference = ART-01.total_po)
# ══════════════════════════════════════════════════

def _update_payment_status(expediente):
    """
    §L3: SUM(payments) >= invoice_total → paid.
    Sprint 5: COMISION uses expected commission (total_po * comision_pactada / 100) as reference.
    """
    total_paid = expediente.payment_lines.aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    # Get reference total based on mode
    reference_total = Decimal('0')

    if expediente.mode == 'COMISION':
        # COMISION: reference = expected commission (ART-01 total * ART-02 comision_pactada / 100)
        art01 = _get_artifact(expediente, 'ART-01')
        art02 = _get_artifact(expediente, 'ART-02')

        total_po = Decimal('0')
        if art01:
            if 'total_po' in art01.payload:
                total_po = Decimal(str(art01.payload['total_po']))
            elif 'total' in art01.payload:
                total_po = Decimal(str(art01.payload['total']))

        comision_pactada = Decimal('0')
        if art02 and 'comision_pactada' in art02.payload:
            comision_pactada = Decimal(str(art02.payload['comision_pactada']))

        reference_total = (total_po * comision_pactada) / Decimal('100')
    else:
        # FULL: reference = ART-09 total_client_view
        art09 = _get_artifact(expediente, 'ART-09')
        if art09:
            if 'total_client_view' in art09.payload:
                reference_total = Decimal(str(art09.payload['total_client_view']))
            elif 'total' in art09.payload:
                reference_total = Decimal(str(art09.payload['total']))

    if reference_total <= 0:
        if total_paid > 0:
            expediente.payment_status = 'partial'
        else:
            expediente.payment_status = 'pending'
    elif total_paid >= reference_total:
        expediente.payment_status = 'paid'
    elif total_paid > 0:
        expediente.payment_status = 'partial'
    else:
        expediente.payment_status = 'pending'

    expediente.save(update_fields=['payment_status'])


# ══════════════════════════════════════════════════
# C19 & C20: Artifact Correction (Sprint 2)
# ══════════════════════════════════════════════════

def _is_post_transition(expediente, artifact_type):
    """BUG 8: Check if artifact is a precondition for an already executed transition."""
    created_in_state = None
    for cmd, spec in COMMAND_SPEC.items():
        if spec.get('creates_art') == artifact_type:
            created_in_state = spec.get('required_state')
            break

    return created_in_state and expediente.status != created_in_state

def supersede_artifact(old_artifact_id, new_payload, user):
    with transaction.atomic():
        try:
            old_art = ArtifactInstance.objects.select_for_update().get(pk=old_artifact_id)
        except ArtifactInstance.DoesNotExist:
            raise CommandValidationError("Artifact not found")

        expediente = Expediente.objects.select_for_update().get(pk=old_art.expediente_id)

        if old_art.status != 'completed':
            raise CommandValidationError(f"Cannot supersede artifact in status {old_art.status}")

        if expediente.status in TERMINAL_STATES:
            raise CommandValidationError("Cannot supersede artifact in terminal state Expediente")

        if _is_post_transition(expediente, old_art.artifact_type) and not expediente.is_blocked:
            from rest_framework.exceptions import APIException
            class Conflict409(APIException):
                status_code = 409
                default_detail = 'Expediente must be blocked (C17) before correcting an artifact in a downstream state.'
            raise Conflict409()

        new_art = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type=old_art.artifact_type,
            status='completed',
            payload=new_payload,
            supersedes=old_art
        )

        old_art.status = 'superseded'
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

        return expediente, new_art, event


def void_artifact(old_artifact_id, user):
    with transaction.atomic():
        try:
            old_art = ArtifactInstance.objects.select_for_update().get(pk=old_artifact_id)
        except ArtifactInstance.DoesNotExist:
            raise CommandValidationError("Artifact not found")

        expediente = Expediente.objects.select_for_update().get(pk=old_art.expediente_id)

        if old_art.artifact_type not in ['ART-09', 'ART-12']:
            raise CommandValidationError("Only ART-09 and ART-12 can be voided in MVP.")

        if old_art.status != 'completed':
            raise CommandValidationError(f"Cannot void artifact in status {old_art.status}")

        if expediente.status in TERMINAL_STATES:
            raise CommandValidationError("Cannot void artifact in terminal state Expediente")

        if _is_post_transition(expediente, old_art.artifact_type) and not expediente.is_blocked:
            from rest_framework.exceptions import APIException
            class Conflict409(APIException):
                status_code = 409
                default_detail = 'Expediente must be blocked (C17) before voiding an artifact in a downstream state.'
            raise Conflict409()

        old_art.status = 'void'
        old_art.save(update_fields=['status'])

        event = _create_event(
            expediente,
            event_type='artifact.voided',
            emitted_by='C20:VoidArtifact',
            payload={
                'artifact_id': str(old_art.artifact_id),
            }
        )

        return expediente, old_art, event


# ══════════════════════════════════════════════════
# UI HELPERS (Sprint 3)
# ══════════════════════════════════════════════════

def get_available_commands(expediente, user):
    """
    Returns available actions categorized for UI.
    Sprint 4: includes C22, C23, C24
    """
    actions = {
        'primary': [],
        'secondary': [],
        'ops': []
    }

    PRIMARY_IDS = {'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13'}
    SECONDARY_IDS = {'C14', 'C16'}

    for cmd_id in sorted(COMMAND_SPEC.keys(), key=lambda x: int(x[1:])):
        if cmd_id == 'C1':
            continue

        spec = COMMAND_SPEC[cmd_id]

        req_state = spec.get('required_state')
        not_in = spec.get('not_in_state', [])

        show_in_ui = False
        if not req_state or req_state == expediente.status:
            show_in_ui = True

        if cmd_id in SECONDARY_IDS:
             show_in_ui = True

        if expediente.status in not_in:
            show_in_ui = False

        if expediente.status in TERMINAL_STATES and cmd_id not in ['C15', 'C17', 'C18', 'C19', 'C20', 'C21']:
             show_in_ui = False

        if not show_in_ui:
            continue

        enabled = True
        disabled_reason = None
        try:
            can_execute_command(expediente, cmd_id, user)
        except Exception as e:
            enabled = False
            disabled_reason = str(e)

        cmd_info = {
            'id': cmd_id,
            'name': spec['name'],
            'enabled': enabled,
        }
        if disabled_reason:
            cmd_info['disabled_reason'] = disabled_reason
        if 'creates_art' in spec:
            cmd_info['creates_artifact'] = spec['creates_art']

        if cmd_id == 'C15':
            cmd_info['fields'] = ['cost_type', 'amount', 'currency', 'phase', 'description', 'visibility']
        elif cmd_id == 'C21':
            cmd_info['fields'] = ['payment_type', 'amount', 'currency', 'reference', 'date']
        elif cmd_id == 'C23':
            cmd_info['fields'] = ['mode', 'carrier', 'route', 'estimated_days', 'estimated_cost', 'currency', 'valid_until', 'source']
        elif cmd_id == 'C24':
            cmd_info['fields'] = ['selected_option_id']

        if cmd_id in PRIMARY_IDS:
            actions['primary'].append(cmd_info)
        elif cmd_id in SECONDARY_IDS:
            actions['secondary'].append(cmd_info)
        else:
            actions['ops'].append(cmd_info)

    return actions


# ══════════════════════════════════════════════════
# Sprint 4 S4-02: Costs Doble Vista functions
# ══════════════════════════════════════════════════

def get_costs(expediente, view='internal'):
    """Get costs filtered by visibility view."""
    qs = expediente.cost_lines.all()
    if view == 'client':
        qs = qs.filter(visibility='client')
    # internal = all costs (CEO sees everything)
    return qs


def get_costs_summary(expediente):
    """Get aggregated cost summary with margin."""
    total_internal = expediente.cost_lines.aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    total_client = expediente.cost_lines.filter(
        visibility='client'
    ).aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    # Get invoiced total from ART-09
    total_invoiced = Decimal('0')
    art09 = _get_artifact(expediente, 'ART-09')
    if art09 and 'total_client_view' in art09.payload:
        total_invoiced = Decimal(str(art09.payload['total_client_view']))

    margin = total_invoiced - total_internal if total_invoiced > 0 else Decimal('0')
    margin_pct = (margin / total_invoiced * 100) if total_invoiced > 0 else Decimal('0')

    return {
        'total_internal': float(total_internal),
        'total_client': float(total_client),
        'total_invoiced': float(total_invoiced),
        'margin': float(margin),
        'margin_pct': float(margin_pct),
    }


# ══════════════════════════════════════════════════
# Sprint 4 S4-03: Invoice helpers
# ══════════════════════════════════════════════════

def get_invoice_suggestion(expediente):
    """Pre-calculate suggested invoice total from client-visible costs."""
    total_client = expediente.cost_lines.filter(
        visibility='client'
    ).aggregate(
        total=models_Sum('amount')
    )['total'] or Decimal('0')

    # Get currency from proforma or costs
    art02 = _get_artifact(expediente, 'ART-02')
    currency = 'USD'
    if art02 and 'currency' in art02.payload:
        currency = art02.payload['currency']

    return {
        'suggested_total': float(total_client),
        'currency': currency,
        'cost_breakdown': {
            'total_client_costs': float(total_client),
        }
    }


def get_invoice(expediente, view='internal'):
    """Get invoice (ART-09) payload filtered by view."""
    art09 = _get_artifact(expediente, 'ART-09')
    if not art09:
        return None

    payload = dict(art09.payload)

    if view == 'client':
        # Remove CEO-only fields
        for field in ('total_internal_view', 'margin', 'margin_pct'):
            payload.pop(field, None)

    return payload


# ══════════════════════════════════════════════════
# Sprint 4 S4-05: Financial Comparison
# ══════════════════════════════════════════════════

def calculate_financial_comparison(expediente):
    """
    Calculate real vs counterfactual financial scenario.
    - If real=FULL: needs ART-09. Counterfactual simulates COMISION.
    - If real=COMISION: needs ART-02+CostLines. Counterfactual simulates FULL.
    """
    actual_mode = expediente.mode or 'FULL'

    if actual_mode == 'FULL':
        # Real scenario: FULL
        art09 = _get_artifact(expediente, 'ART-09')
        if not art09:
            raise CommandValidationError('Insufficient data for comparison: ART-09 required for FULL mode.')

        revenue_actual = Decimal(str(art09.payload.get('total_client_view', 0)))
        cost_actual = expediente.cost_lines.aggregate(
            total=models_Sum('amount')
        )['total'] or Decimal('0')
        margin_actual = revenue_actual - cost_actual
        margin_pct_actual = (margin_actual / revenue_actual * 100) if revenue_actual > 0 else Decimal('0')

        # Counterfactual: COMISION
        art02 = _get_artifact(expediente, 'ART-02')
        if not art02:
            raise CommandValidationError('Insufficient data for comparison: ART-02 required.')

        comision_pactada = Decimal(str(art02.payload.get('comision_pactada', 0)))
        if comision_pactada <= 0:
            raise CommandValidationError('Insufficient data for comparison: comision_pactada not found in ART-02.')

        art01 = _get_artifact(expediente, 'ART-01')
        total_po = Decimal(str(art01.payload.get('total_po', art01.payload.get('total', 0)))) if art01 else Decimal('0')

        revenue_counter = comision_pactada * total_po / 100
        cost_counter = Decimal('0')  # MWT no compra en comisión
        margin_counter = revenue_counter
        margin_pct_counter = Decimal('100') if revenue_counter > 0 else Decimal('0')

        counterfactual_mode = 'COMISION'

    elif actual_mode == 'COMISION':
        # Real scenario: COMISION
        art02 = _get_artifact(expediente, 'ART-02')
        if not art02:
            raise CommandValidationError('Insufficient data for comparison: ART-02 required for COMISION mode.')

        comision_pactada = Decimal(str(art02.payload.get('comision_pactada', 0)))
        if comision_pactada <= 0:
            raise CommandValidationError('Insufficient data for comparison: comision_pactada not found in ART-02.')

        art01 = _get_artifact(expediente, 'ART-01')
        total_po = Decimal(str(art01.payload.get('total_po', art01.payload.get('total', 0)))) if art01 else Decimal('0')

        revenue_actual = comision_pactada * total_po / 100
        cost_actual = Decimal('0')
        margin_actual = revenue_actual
        margin_pct_actual = Decimal('100') if revenue_actual > 0 else Decimal('0')

        # Counterfactual: FULL
        total_internal = expediente.cost_lines.aggregate(
            total=models_Sum('amount')
        )['total'] or Decimal('0')

        # Estimate client view from total_po (what MWT would charge)
        revenue_counter = total_po
        cost_counter = total_internal
        margin_counter = revenue_counter - cost_counter
        margin_pct_counter = (margin_counter / revenue_counter * 100) if revenue_counter > 0 else Decimal('0')

        counterfactual_mode = 'FULL'
    else:
        raise CommandValidationError('Insufficient data for comparison: unknown mode.')

    delta_margin = margin_actual - margin_counter
    if delta_margin > 0:
        recommendation = f'{actual_mode} was better by ${abs(float(delta_margin)):.2f}'
    elif delta_margin < 0:
        recommendation = f'{counterfactual_mode} would have been better by ${abs(float(delta_margin)):.2f}'
    else:
        recommendation = 'Both modes yield the same margin'

    return {
        'expediente_id': str(expediente.expediente_id),
        'actual_mode': actual_mode,
        'actual': {
            'revenue': float(revenue_actual),
            'cost': float(cost_actual),
            'margin': float(margin_actual),
            'margin_pct': float(margin_pct_actual),
        },
        'counterfactual_mode': counterfactual_mode,
        'counterfactual': {
            'revenue': float(revenue_counter),
            'cost': float(cost_counter),
            'margin': float(margin_counter),
            'margin_pct': float(margin_pct_counter),
        },
        'delta': {
            'margin': float(delta_margin),
            'recommendation': recommendation,
        },
    }


# ══════════════════════════════════════════════════
# Sprint 4 S4-08: Mirror PDF Generation
# ══════════════════════════════════════════════════

def generate_mirror_pdf(expediente):
    """
    Generate a client-facing PDF with only visibility=client data.
    Returns HTML string to be rendered by weasyprint.
    """
    # Get client-visible costs
    client_costs = expediente.cost_lines.filter(visibility='client')

    # Get ART-09 if exists
    art09 = _get_artifact(expediente, 'ART-09')

    # Get ART-05 for tracking info
    art05 = _get_artifact(expediente, 'ART-05')

    # Get timeline events
    events = EventLog.objects.filter(
        aggregate_id=expediente.expediente_id,
        aggregate_type='expediente',
        event_type__in=[
            'expediente.created', 'expediente.state_changed',
            'expediente.closed',
        ]
    ).order_by('occurred_at')

    # Get product info from ART-01
    art01 = _get_artifact(expediente, 'ART-01')

    if not art01 and not client_costs.exists():
        return None  # No data to show

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ background: #013A57; color: white; padding: 20px; margin: -40px -40px 30px -40px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header .subtitle {{ color: #75CBB3; font-size: 14px; }}
            .section {{ margin-bottom: 25px; }}
            .section h2 {{ color: #013A57; border-bottom: 2px solid #75CBB3; padding-bottom: 5px; font-size: 18px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #013A57; color: white; padding: 8px; text-align: left; font-size: 12px; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; font-size: 12px; }}
            .total-row {{ font-weight: bold; background: #f5f5f5; }}
            .timeline {{ list-style: none; padding: 0; }}
            .timeline li {{ padding: 8px 0; border-left: 3px solid #75CBB3; padding-left: 15px; margin-left: 10px; }}
            .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
            .badge-mint {{ background: #75CBB3; color: #013A57; }}
            .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>MWT.ONE — Expediente</h1>
            <div class="subtitle">
                Ref: EXP-{str(expediente.expediente_id)[:8]} |
                Marca: {expediente.brand} |
                Cliente: {expediente.client.legal_name} |
                Fecha: {timezone.now().strftime('%d/%m/%Y')}
            </div>
        </div>
    """

    # Products section
    if art01:
        html += """
        <div class="section">
            <h2>Productos</h2>
            <table>
                <tr><th>Producto</th><th>Cantidad</th><th>Referencia</th></tr>
        """
        items = art01.payload.get('items', art01.payload.get('lines', []))
        if isinstance(items, list):
            for item in items:
                name = item.get('product', item.get('sku_alias', item.get('description', 'N/A')))
                qty = item.get('qty', item.get('quantity', 'N/A'))
                ref = item.get('reference', item.get('sku', 'N/A'))
                html += f"<tr><td>{name}</td><td>{qty}</td><td>{ref}</td></tr>"
        html += "</table></div>"

    # Client costs section
    if client_costs.exists():
        html += """
        <div class="section">
            <h2>Costos</h2>
            <table>
                <tr><th>Tipo</th><th>Monto</th><th>Moneda</th><th>Fase</th></tr>
        """
        total = Decimal('0')
        for cost in client_costs:
            html += f"<tr><td>{cost.cost_type}</td><td>{cost.amount}</td><td>{cost.currency}</td><td>{cost.phase}</td></tr>"
            total += cost.amount
        html += f'<tr class="total-row"><td>Total</td><td>{total}</td><td></td><td></td></tr>'
        html += "</table></div>"

    # Invoice section
    if art09:
        html += f"""
        <div class="section">
            <h2>Factura</h2>
            <table>
                <tr><th>Consecutivo</th><th>Total</th><th>Moneda</th></tr>
                <tr>
                    <td>{art09.payload.get('consecutive', 'N/A')}</td>
                    <td>{art09.payload.get('total_client_view', 'N/A')}</td>
                    <td>{art09.payload.get('currency', 'N/A')}</td>
                </tr>
            </table>
        </div>
        """

    # Timeline section
    if events.exists():
        html += '<div class="section"><h2>Timeline</h2><ul class="timeline">'
        for ev in events:
            date = ev.occurred_at.strftime('%d/%m/%Y %H:%M')
            html += f'<li><span class="badge badge-mint">{ev.event_type}</span> — {date}</li>'
        html += '</ul></div>'

    # Tracking section
    if art05:
        carrier = art05.payload.get('carrier', 'N/A')
        tracking = art05.payload.get('tracking_number', art05.payload.get('tracking', 'N/A'))
        html += f"""
        <div class="section">
            <h2>Tracking</h2>
            <p>Carrier: {carrier} | Tracking: {tracking}</p>
        </div>
        """

    html += """
        <div class="footer">
            <p>Documento generado por MWT.ONE — Confidencial</p>
        </div>
    </body>
    </html>
    """

    return html
