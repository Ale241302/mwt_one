from decimal import Decimal
from apps.expedientes.models import PaymentLine, CostLine
from .helpers import _update_payment_status

def handle_c15(expediente, payload, env=None):
    # Registrar Gasto (Financial)
    cost = CostLine(
        expediente=expediente,
        cost_type=payload.get('cost_type', ''),
        amount=Decimal(str(payload.get('amount', '0'))),
        currency=payload.get('currency', 'USD'),
        phase=payload.get('phase', ''),
        description=payload.get('description', ''),
        cost_category=payload.get('cost_category', 'landed_cost'),
        cost_behavior=payload.get('cost_behavior'),
        base_currency=payload.get('base_currency', 'USD'),
    )

    if payload.get('exchange_rate') and payload.get('currency'):
        if payload['currency'] == (payload.get('base_currency') or 'USD'):
            cost.exchange_rate = Decimal('1.0')
            cost.amount_base_currency = cost.amount
        else:
            cost.exchange_rate = Decimal(str(payload['exchange_rate']))
            cost.amount_base_currency = cost.amount * cost.exchange_rate
    elif payload.get('currency') == (payload.get('base_currency') or 'USD'):
        cost.exchange_rate = Decimal('1.0')
        cost.amount_base_currency = cost.amount

    cost.save()

def handle_c21(expediente, payload, env=None):
    # Registrar Pago (Financial)
    # This was a complex logic in services.py 420:
    PaymentLine.objects.create(
        expediente=expediente,
        amount=payload.get('amount'),
        method=payload.get('method'),
        reference=payload.get('reference')
    )
    _update_payment_status(expediente)
