from django.db.models import Sum
from apps.expedientes.models import CostLine

def get_costs(expediente, view='internal'):
    qs = expediente.cost_lines.all()
    if view == 'client':
        qs = qs.filter(visibility='client')
    return qs

def get_costs_summary(expediente):
    # Sum internal vs client costs
    internal = expediente.cost_lines.aggregate(total=Sum('amount'))['total'] or 0
    client = expediente.cost_lines.filter(visibility='client').aggregate(total=Sum('amount'))['total'] or 0
    return {
        'internal_total': float(internal),
        'client_total': float(client),
        'margin': float(client - internal)
    }

def get_invoice_suggestion(expediente):
    # Logic for ART-09 suggestion
    return {'suggested_items': []}

def get_invoice(expediente, view='internal'):
    art09 = expediente.artifacts.filter(artifact_type='ART-09', status='completed').first()
    if not art09:
        return None
    return art09.payload

def calculate_financial_comparison(expediente):
    return {'actual': {}, 'estimated': {}}

def can_execute_command(expediente, cmd_id, user):
    from .constants import COMMAND_SPEC
    if cmd_id not in COMMAND_SPEC:
        return False

    cmd_config = COMMAND_SPEC[cmd_id]
    req_status = cmd_config.get('requires_status')
    if req_status and expediente.status != req_status:
        return False

    # Blocked check
    if expediente.is_blocked and cmd_id not in ['C18', 'C19', 'C20']:
        return False

    return True

def get_available_commands(expediente, user):
    from .constants import COMMAND_SPEC
    available = []
    for cmd_id in COMMAND_SPEC:
        if can_execute_command(expediente, cmd_id, user):
            available.append(cmd_id)
    return available


# ─────────────────────────────────────────────────────────────────────
# Sprint 5 Query Functions (migrated from services_sprint5.py)
# ─────────────────────────────────────────────────────────────────────

from django.db.models import Count, Avg
from apps.expedientes.models import Expediente, ArtifactInstance, LogisticsOption

def get_logistics_suggestions(expediente):
    """
    S5-07: GET /api/expedientes/{id}/logistics-suggestions/
    Returns ranked suggestions from historical data.
    Requires >=5 completed expedientes with ART-19.
    """
    closed_expedientes = Expediente.objects.filter(status='CERRADO')
    selected_options = LogisticsOption.objects.filter(
        artifact_instance__expediente__in=closed_expedientes,
        is_selected=True,
    )

    if selected_options.count() < 5:
        return {
            'suggestions': [],
            'message': 'Insufficient historical data (minimum 5 completed routes required).',
            'count': selected_options.count(),
        }

    stats = (
        selected_options
        .values('carrier', 'mode', 'route')
        .annotate(
            frequency=Count('id'),
            avg_cost=Avg('estimated_cost'),
            avg_days=Avg('estimated_days'),
        )
        .order_by('-frequency', 'avg_cost', 'avg_days')
    )

    suggestions = [
        {
            'carrier': s['carrier'],
            'mode': s['mode'],
            'route': s['route'],
            'frequency': s['frequency'],
            'avg_cost': str(s['avg_cost']) if s['avg_cost'] else None,
            'avg_days': float(s['avg_days']) if s['avg_days'] else None,
        }
        for s in stats[:10]
    ]

    return {
        'suggestions': suggestions,
        'message': f'Based on {selected_options.count()} historical routes.',
        'count': len(suggestions),
    }


def get_handoff_suggestion(expediente):
    """
    S5-06: Returns transfer suggestion data if expediente is CERRADO
    and has nodo_destino assigned. CEO uses this to create transfer via C30.
    """
    if expediente.status != 'CERRADO':
        return {'has_suggestion': False, 'reason': 'Expediente not closed'}

    if not expediente.nodo_destino:
        return {'has_suggestion': False, 'reason': 'No destination node assigned'}

    nodo = expediente.nodo_destino
    items = []
    art01 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-01', status='completed'
    ).order_by('-created_at').first()

    if art01 and art01.payload:
        oc_items = art01.payload.get('items', [])
        for item in oc_items:
            items.append({
                'sku': item.get('sku', item.get('description', 'N/A')),
                'quantity': item.get('quantity', 1),
            })

    if not items:
        items = [{'sku': f'EXP-{str(expediente.expediente_id)[:8]}', 'quantity': 1}]

    return {
        'has_suggestion': True,
        'message': f'Producto entregado a {nodo.name}. ¿Crear transfer?',
        'transfer_data': {
            'from_node': str(nodo.node_id),
            'source_expediente': str(expediente.expediente_id),
            'items': items,
        },
        'node': {
            'node_id': str(nodo.node_id),
            'name': nodo.name,
            'node_type': nodo.node_type,
            'location': nodo.location,
        },
    }


def get_liquidation_payment_suggestion(expediente):
    """
    S5-10: When ART-10 liquidation is reconciled and has lines matched
    to proformas of this expediente, suggest registering payment via C21.
    """
    from decimal import Decimal
    from django.db.models import Sum as DjangoSum

    if expediente.mode != 'COMISION':
        return {'has_suggestion': False, 'reason': 'Only applicable for COMISION mode'}

    # Import here to avoid circular dependency
    try:
        from apps.liquidations.models import LiquidationLine
        from apps.liquidations.enums_exp import LiquidationStatus, MatchStatus
    except ImportError:
        return {'has_suggestion': False, 'reason': 'Liquidations module not available'}

    matched_lines = LiquidationLine.objects.filter(
        matched_expediente=expediente,
        liquidation__status=LiquidationStatus.RECONCILED,
        match_status=MatchStatus.MATCHED,
    ).select_related('liquidation')

    if not matched_lines.exists():
        return {'has_suggestion': False, 'reason': 'No reconciled liquidation lines for this expediente'}

    art01 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-01', status='completed'
    ).order_by('-created_at').first()
    art02 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-02', status='completed'
    ).order_by('-created_at').first()

    total_po = Decimal('0')
    if art01 and 'total_po' in art01.payload:
        total_po = Decimal(str(art01.payload['total_po']))
    elif art01 and 'total' in art01.payload:
        total_po = Decimal(str(art01.payload['total']))

    comision_pactada = Decimal('0')
    if art02 and 'comision_pactada' in art02.payload:
        comision_pactada = Decimal(str(art02.payload['comision_pactada']))

    expected_commission = (total_po * comision_pactada) / Decimal('100')

    total_paid = expediente.payment_lines.aggregate(
        total=DjangoSum('amount')
    )['total'] or Decimal('0')

    remaining = expected_commission - total_paid

    suggestions = []
    for line in matched_lines:
        suggestions.append({
            'liquidation_id': line.liquidation.liquidation_id,
            'period': line.liquidation.period,
            'commission_amount': str(line.commission_amount),
            'marluvas_reference': line.marluvas_reference,
            'c21_data': {
                'amount': str(line.commission_amount),
                'currency': line.currency or 'USD',
                'method': 'liquidacion_marluvas',
                'reference': line.liquidation.liquidation_id,
            },
        })

    return {
        'has_suggestion': True,
        'expected_commission': str(expected_commission),
        'total_paid': str(total_paid),
        'remaining': str(remaining),
        'is_partial': total_paid > Decimal('0') and total_paid < expected_commission,
        'payment_status': expediente.payment_status,
        'suggestions': suggestions,
    }
