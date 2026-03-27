# Sprint 18 - T1.8 recalculate_expediente_credit() + T1.9 sync CreditExposure
from decimal import Decimal
from django.utils import timezone


def recalculate_expediente_credit(expediente):
    """
    UNICA fuente de verdad para credit_exposure y credit_released.
    Nadie mas puede setear credit_released.
    """
    total_lines = sum(
        (line.unit_price * line.quantity)
        for line in expediente.product_lines.all()
    )
    total_paid = sum(
        p.amount_paid
        for p in expediente.pagos.filter(credit_status='CONFIRMED')
    )
    total_lines = total_lines if total_lines else Decimal('0.00')
    total_paid = total_paid if total_paid else Decimal('0.00')

    expediente.credit_exposure = total_lines - total_paid
    expediente.credit_released = (expediente.credit_exposure <= Decimal('0.00'))
    expediente.save(update_fields=['credit_exposure', 'credit_released'])


def sync_credit_exposure_and_log(expediente, user=None):
    """
    Wrapper que detecta cambio en credit_released y sincroniza CreditExposure
    del cliente + crea EventLog si cambia.
    Llamar DESPUES de confirmar un pago.
    """
    from apps.expedientes.models import EventLog
    from django.utils import timezone
    import uuid

    old_released = expediente.credit_released
    recalculate_expediente_credit(expediente)

    if expediente.credit_released != old_released:
        # Intentar actualizar CreditExposure del cliente (si existe el modelo)
        try:
            from apps.clientes.models import CreditExposure
            CreditExposure.objects.filter(
                client=expediente.client
            ).update(
                total_exposure=_get_total_client_exposure(expediente.client),
                updated_at=timezone.now()
            )
        except Exception:
            pass  # modelo puede no existir en todos los tenants

        # Crear EventLog del cambio de credito
        try:
            EventLog.objects.create(
                event_type='credit_change',
                aggregate_type='EXP',
                aggregate_id=expediente.expediente_id,
                payload={
                    'credit_released': expediente.credit_released,
                    'credit_exposure': str(expediente.credit_exposure),
                    'user': str(user) if user else None,
                },
                occurred_at=timezone.now(),
                emitted_by='recalculate_expediente_credit',
                correlation_id=uuid.uuid4(),
            )
        except Exception:
            pass


def _get_total_client_exposure(client):
    from apps.expedientes.models import Expediente
    from decimal import Decimal
    total = Decimal('0.00')
    for exp in Expediente.objects.filter(client=client, credit_released=False):
        if exp.credit_exposure:
            total += exp.credit_exposure
    return total
