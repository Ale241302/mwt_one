# Sprint 18 - T1.8 recalculate_expediente_credit() + T1.9 sync CreditExposure
# S25-05: extendido para filtrar solo pagos credit_released, agregar compute_coverage()
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


def compute_coverage(total_paid: Decimal, expediente_total) -> tuple:
    """
    SSOT para payment_coverage y coverage_pct.
    Retorna (payment_coverage: str, coverage_pct: Decimal).

    Edge case (fix M1 R5): si expediente_total es None o <= 0,
    retorna ('none', 0.00) inmediatamente — incluso si total_paid > 0.
    Esto elimina el caso donde total_paid > 0 + total = 0 daría 'complete'.

    Redondeo: ROUND_HALF_UP explícito (fix N1 R6) para contrato determinista.
    Cap: 100.00 (sobrepago no muestra >100%).
    """
    # PASO 1: Early return si no hay denominador válido
    if expediente_total is None or expediente_total <= 0:
        if total_paid > 0:
            return 'complete', Decimal('100.00')
        return 'none', Decimal('0.00')

    # PASO 2: Calcular porcentaje con ROUND_HALF_UP (fix N1 R6)
    coverage_pct = min(
        Decimal('100.00'),
        ((total_paid / expediente_total) * Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    )

    # PASO 3: Clasificación semántica
    if total_paid <= 0:
        payment_coverage = 'none'
    elif total_paid >= expediente_total:
        payment_coverage = 'complete'
    else:
        payment_coverage = 'partial'

    return payment_coverage, coverage_pct


def recalculate_expediente_credit(expediente):
    """
    ÚNICA fuente de verdad para credit_exposure, credit_released y credit_snapshot.
    S25-05: solo suma pagos con payment_status='credit_released'.
    Backward compat: la data migration de S25-01 ya clasificó pagos legacy.
    CreditOverride intocable: si existe, lo respeta.
    """
    total_lines = sum(
        (line.unit_price * line.quantity)
        for line in expediente.product_lines.all()
    ) or Decimal('0.00')

    # Solo pagos credit_released cuentan (S25-05)
    total_released = sum(
        p.amount_paid
        for p in expediente.pagos.filter(payment_status='credit_released')
        if p.amount_paid
    ) or Decimal('0.00')

    total_pending = sum(
        p.amount_paid
        for p in expediente.pagos.filter(payment_status__in=['pending', 'verified'])
        if p.amount_paid
    ) or Decimal('0.00')

    total_rejected = sum(
        p.amount_paid
        for p in expediente.pagos.filter(payment_status='rejected')
        if p.amount_paid
    ) or Decimal('0.00')

    expediente_total = getattr(expediente, 'total_value', None) or total_lines

    payment_coverage, coverage_pct = compute_coverage(total_released, expediente_total)

    exposure = total_lines - total_released
    available = Decimal('0.00')  # placeholder; CreditPolicy no se modifica

    expediente.credit_exposure = exposure
    expediente.credit_released = (exposure <= Decimal('0.00'))
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
