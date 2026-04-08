from decimal import Decimal
from django.utils import timezone
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
    """Registrar Pago (Financial) — C21.

    Crea un PaymentLine con TODOS los campos NOT NULL requeridos por el modelo.
    Campos anteriormente ausentes que causaban la violación de constraint:
      - registered_at       → timezone.now() o valor del payload
      - currency            → payload.get('currency', 'USD')
      - registered_by_type  → 'CEO' si superuser, 'AGENT' en otro caso
      - registered_by_id    → str(user.pk) o 'system'
    """
    user = env.get('user') if env else None

    # Determinar tipo/id de registrador
    if user and hasattr(user, 'is_superuser') and user.is_superuser:
        registered_by_type = 'CEO'
    elif user and user.is_authenticated:
        registered_by_type = 'AGENT'
    else:
        registered_by_type = 'AGENT'

    registered_by_id = str(user.pk) if (user and user.is_authenticated) else 'system'

    # registered_at: acepta override del payload (para backfills), por defecto now()
    raw_registered_at = payload.get('registered_at')
    if raw_registered_at:
        from django.utils.dateparse import parse_datetime
        registered_at = parse_datetime(str(raw_registered_at)) or timezone.now()
    else:
        registered_at = timezone.now()

    PaymentLine.objects.create(
        expediente=expediente,
        amount=Decimal(str(payload.get('amount', '0'))),
        currency=payload.get('currency', 'USD'),
        method=payload.get('method', ''),
        reference=payload.get('reference', ''),
        registered_at=registered_at,
        registered_by_type=registered_by_type,
        registered_by_id=registered_by_id,
    )
    _update_payment_status(expediente)
