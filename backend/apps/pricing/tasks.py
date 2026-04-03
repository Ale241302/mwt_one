# Sprint 22 - S22-09/S22-10: Celery tasks para recálculo de assignments y alerta de margen
from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def recalculate_assignments_for_brand(self, brand_id):
    """
    S22-09: Recalcula todos los CPAs activos de un brand.
    Se dispara automáticamente cuando se activa una pricelist.
    CRÍTICO: usa skip_cache=True para no leer el propio cache.

    S22-10: Al final, emite alerta de margen si margin < Brand.min_margin_alert_pct.
    """
    try:
        from apps.pricing.models import ClientProductAssignment
        from apps.pricing.services import resolve_client_price
        from apps.brands.models import Brand
        from django.utils import timezone
        from decimal import Decimal

        brand = Brand.objects.get(pk=brand_id)
        assignments = ClientProductAssignment.objects.filter(
            brand_sku__brand_id=brand_id,
            is_active=True,
        ).select_related('brand_sku', 'client_subsidiary')

        updated_count = 0
        margin_alerts = []

        for cpa in assignments:
            try:
                # CRÍTICO: skip_cache=True — sin esto lee su propio cache
                result = resolve_client_price(
                    product=cpa.brand_sku,
                    client=None,
                    brand=brand,
                    brand_sku_id=cpa.brand_sku_id,
                    client_subsidiary_id=cpa.client_subsidiary_id,
                    skip_cache=True,
                )
                if result:
                    cpa.cached_client_price = result['price']
                    cpa.cached_base_price = result.get('base_price')
                    cpa.cached_pricelist_version_id = result.get('pricelist_version')
                    cpa.cached_at = timezone.now()
                    cpa.save(update_fields=[
                        'cached_client_price',
                        'cached_base_price',
                        'cached_pricelist_version',
                        'cached_at',
                    ])
                    updated_count += 1

                    # S22-10: Alerta de margen
                    _check_margin_alert(
                        cpa=cpa,
                        brand=brand,
                        client_price=result['price'],
                        base_price=result.get('base_price'),
                        margin_alerts=margin_alerts,
                    )
            except Exception:
                pass

        # EventLog al completar
        try:
            from apps.audit.models import EventLog
            EventLog.objects.create(
                event_type='assignments_recalculated',
                description=(
                    f"Recálculo completado para brand {brand_id}. "
                    f"CPAs actualizados: {updated_count}. "
                    f"Alertas de margen: {len(margin_alerts)}."
                ),
            )
        except Exception:
            pass

        return {
            'brand_id': brand_id,
            'updated': updated_count,
            'margin_alerts': len(margin_alerts),
        }

    except Exception as exc:
        raise self.retry(exc=exc)


def _check_margin_alert(cpa, brand, client_price, base_price, margin_alerts):
    """
    S22-10: Compara precio cacheado con costo base.
    Si margin < Brand.min_margin_alert_pct (y el campo no es NULL)
    → crea notificación tipo 'margin_alert'.
    """
    from decimal import Decimal
    try:
        if brand.min_margin_alert_pct is None:
            return
        if not client_price or not base_price or base_price == 0:
            return
        margin_pct = ((client_price - base_price) / base_price) * Decimal('100')
        if margin_pct < brand.min_margin_alert_pct:
            margin_alerts.append({
                'cpa_id': cpa.pk,
                'brand_sku_id': cpa.brand_sku_id,
                'client_subsidiary_id': cpa.client_subsidiary_id,
                'margin_pct': float(margin_pct),
                'threshold': float(brand.min_margin_alert_pct),
            })
            # Crear notificación
            try:
                from apps.core.models import Notification
                Notification.objects.create(
                    notification_type='margin_alert',
                    title=f"Alerta de margen: {cpa.brand_sku}",
                    body=(
                        f"Margen {margin_pct:.2f}% está por debajo del umbral "
                        f"{brand.min_margin_alert_pct}% para "
                        f"SKU {cpa.brand_sku_id} / cliente {cpa.client_subsidiary_id}."
                    ),
                    related_object_id=cpa.pk,
                )
            except Exception:
                pass
    except Exception:
        pass
